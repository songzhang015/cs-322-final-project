// drawing.js - handles brush drawing, colors, eraser, etc.

let ctx;
let drawing = false;
let drawingEnabled = true;
let lastX = 0;
let lastY = 0;
let remoteLastX = 0;
let remoteLastY = 0;

let history = [];

// Updated externally by your UI
let currentColor = "black";
let currentSize = 5;
let currentTool = "brush";  // brush | eraser

export function setDrawingEnabled(state) {
    drawingEnabled = state;
}

export function setBrushColor(color) {
    currentColor = color;
}

export function setBrushSize(size) {
    currentSize = size;
}

export function setTool(tool) {
    currentTool = tool;
}

export function clearCanvas() {
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    history = [];
}

function saveState() {
    history.push(ctx.getImageData(0, 0, ctx.canvas.width, ctx.canvas.height));
}

export function undo() {
    if (history.length === 0) return;

    const previous = history.pop();
    ctx.putImageData(previous, 0, 0);
}

export function initCanvas(canvas, socket) {
    ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = false;

    // Stroke smoothing
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    // --- MOUSE EVENTS ---
    canvas.addEventListener("mousedown", (e) => {
        if (!drawingEnabled) return;
        saveState();

        const x = e.offsetX;
        const y = e.offsetY;

        if (currentTool === "fill") {
            fillBucket(x, y);

            socket.emit("fill", { x, y, color: currentColor });

            return;
        }

        drawing = true;
        lastX = x;
        lastY = y;
        socket.emit("startPath", {
            x,
            y,
            size: currentSize,
            color: currentColor,
            tool: currentTool
        });
    });

    canvas.addEventListener("click", (e) => {
        if (!drawingEnabled) return;

        const x = e.offsetX;
        const y = e.offsetY;

        // Draw dot locally
        ctx.beginPath();
        ctx.arc(x, y, currentSize / 2, 0, Math.PI * 2);
        ctx.fillStyle = currentTool === "eraser" ? "white" : currentColor;
        ctx.fill();

        // Send to other players
        socket.emit("startPath", {
            x,
            y,
            size: currentSize,
            color: currentColor,
            tool: currentTool
        });
        socket.emit("draw", { x, y });
        socket.emit("endPath", {});
    });

    canvas.addEventListener("mouseup", () => {
        if (!drawingEnabled) return;
        drawing = false;
        solidifyEdges();

        socket.emit("endPath");
    });

    canvas.addEventListener("mouseleave", () => {
        drawing = false;
        solidifyEdges();

        socket.emit("endPath");
    });

    canvas.addEventListener("mousemove", (e) => {
        if (!drawingEnabled) return;
        if (!drawing) return;

        if (currentTool === "brush" || currentTool === "eraser") {
            drawStroke(e.offsetX, e.offsetY);

            socket.emit("draw", {
                x: e.offsetX,
                y: e.offsetY
            });
        }
    });
}

function drawStroke(x, y) {
    ctx.strokeStyle = currentTool === "eraser" ? "white" : currentColor;
    ctx.lineWidth = currentSize;

    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.globalCompositeOperation = "source-over";

    lastX = x;
    lastY = y;
}

function solidifyEdges() {
    const w = ctx.canvas.width;
    const h = ctx.canvas.height;

    const img = ctx.getImageData(0, 0, w, h);
    const pixels = img.data;

    for (let i = 3; i < pixels.length; i += 4) {
        // If pixel is drawn (alpha > 0), force it fully solid
        if (pixels[i] !== 0) {
            pixels[i] = 255;
        }
    }

    ctx.putImageData(img, 0, 0);
}

function normalizeTargetRegion(imageData, w, h, targetColor, tolerance = 8) {
    const d = imageData.data;

    for (let i = 0; i < d.length; i += 4) {
        if (colorsMatch(d.slice(i, i + 4), targetColor, tolerance)) {
            d[i]     = targetColor[0];
            d[i + 1] = targetColor[1];
            d[i + 2] = targetColor[2];
            d[i + 3] = 255;  // fully opaque
        }
    }
}

function colorsMatch(a, b, tolerance = 6) {
    return (
        Math.abs(a[0] - b[0]) <= tolerance &&
        Math.abs(a[1] - b[1]) <= tolerance &&
        Math.abs(a[2] - b[2]) <= tolerance &&
        Math.abs(a[3] - b[3]) <= tolerance
    );
}

function fillBucket(startX, startY) {
    const canvas = ctx.canvas;
    const w = canvas.width;
    const h = canvas.height;

    let imageData = ctx.getImageData(0, 0, w, h);
    let data = imageData.data;

    // Convert currentColor to RGBA
    const temp = document.createElement("canvas").getContext("2d");
    temp.fillStyle = currentColor;
    temp.fillRect(0, 0, 1, 1);
    const fillColor = temp.getImageData(0, 0, 1, 1).data;

    const idx = (x, y) => (y * w + x) * 4;

    const startPos = idx(startX, startY);
    const targetColor = data.slice(startPos, startPos + 4);

    // Detect if fill is unnecessary
    if (colorsMatch(fillColor, targetColor, 1)) return;

    // ---------------------------------------------
    // PHASE 1: INITIAL REGION FINDING
    // ---------------------------------------------
    const tolerance = 10;
    let regionMask = new Uint8Array(w * h);

    // Flood-fill mask generation (4-direction)
    let q = [[startX, startY]];
    regionMask[startY * w + startX] = 1;

    while (q.length) {
        const [x, y] = q.pop();
        const i = idx(x, y);

        const thisColor = data.slice(i, i + 4);
        if (!colorsMatch(thisColor, targetColor, tolerance)) continue;

        // neighbors
        if (x > 0 && !regionMask[y * w + (x - 1)]) {
            regionMask[y * w + (x - 1)] = 1; q.push([x - 1, y]);
        }
        if (x < w - 1 && !regionMask[y * w + (x + 1)]) {
            regionMask[y * w + (x + 1)] = 1; q.push([x + 1, y]);
        }
        if (y > 0 && !regionMask[(y - 1) * w + x]) {
            regionMask[(y - 1) * w + x] = 1; q.push([x, y - 1]);
        }
        if (y < h - 1 && !regionMask[(y + 1) * w + x]) {
            regionMask[(y + 1) * w + x] = 1; q.push([x, y + 1]);
        }
    }

    // ---------------------------------------------
    // PHASE 2: CHECK IF EXPANSION IS NEEDED
    // ---------------------------------------------
    let expansionNeeded = false;

    for (let y = 1; y < h - 1 && !expansionNeeded; y++) {
        for (let x = 1; x < w - 1 && !expansionNeeded; x++) {
            if (!regionMask[y * w + x]) continue;

            // Evaluate 8 neighbors
            for (let dy = -1; dy <= 1; dy++) {
                for (let dx = -1; dx <= 1; dx++) {

                    const nx = x + dx;
                    const ny = y + dy;
                    const ni = idx(nx, ny);
                    const nColor = data.slice(ni, ni + 4);

                    // If neighbor is slightly off but close enough → needs expansion
                    if (!regionMask[ny * w + nx] &&
                        colorsMatch(nColor, targetColor, 20)) {
                        expansionNeeded = true;
                        break;
                    }
                }
            }
        }
    }

    // ---------------------------------------------
    // PHASE 3: MULTIPLY REGION BY EXACTLY 1px (IF NEEDED)
    // ---------------------------------------------
    if (expansionNeeded) {
        let expanded = new Uint8Array(regionMask);

        for (let y = 1; y < h - 1; y++) {
            for (let x = 1; x < w - 1; x++) {
                if (!regionMask[y * w + x]) continue;

                // Expand to 8 neighbors
                expanded[(y - 1) * w + (x - 1)] = 1;
                expanded[(y - 1) * w + x] = 1;
                expanded[(y - 1) * w + (x + 1)] = 1;

                expanded[y * w + (x - 1)] = 1;
                expanded[y * w + (x + 1)] = 1;

                expanded[(y + 1) * w + (x - 1)] = 1;
                expanded[(y + 1) * w + x] = 1;
                expanded[(y + 1) * w + (x + 1)] = 1;
            }
        }

        regionMask = expanded;
    }

    // ---------------------------------------------
    // PHASE 4: PAINT FINAL REGION EXACTLY
    // ---------------------------------------------
    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            if (!regionMask[y * w + x]) continue;

            const i = idx(x, y);
            data[i]     = fillColor[0];
            data[i + 1] = fillColor[1];
            data[i + 2] = fillColor[2];
            data[i + 3] = 255;
        }
    }

    ctx.putImageData(imageData, 0, 0);
}

export function getCanvasImage() {
    return ctx.canvas.toDataURL("image/png");
}

export function loadCanvasFromImage(imgURL) {
    const img = new Image();
    img.src = imgURL;
    img.onload = () => {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        ctx.drawImage(img, 0, 0);
    };
}

export function applyRemoteEvent(type, data) {
    if (type === "startPath" || type === "fill" || type === "clear") {
        saveState();
    }

    switch (type) {
        case "startPath":
            ctx.strokeStyle = data.tool === "eraser" ? "white" : data.color;
            ctx.lineWidth = data.size;
            remoteLastX = data.x;
            remoteLastY = data.y;
            break;

        case "draw":
            ctx.beginPath();
            ctx.moveTo(remoteLastX, remoteLastY);
            ctx.lineTo(data.x, data.y);
            ctx.stroke();
            remoteLastX = data.x;
            remoteLastY = data.y;
            break;

        case "endPath":
            break;

        case "fill":
            setBrushColor(data.color);
            fillBucket(data.x, data.y);
            break;

        case "undo":
            undo();
            break;

        case "clear":
            clearCanvas();
            break;
    }
}