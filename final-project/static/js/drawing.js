// drawing.js - handles brush drawing, colors, eraser, etc.

let ctx;
let drawing = false;
let lastX = 0;
let lastY = 0;

let history = [];

// Updated externally by your UI
let currentColor = "black";
let currentSize = 5;
let currentTool = "brush";  // brush | eraser

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

export function initCanvas(canvas) {
    ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = false;

    // Stroke smoothing
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    // --- MOUSE EVENTS ---
    canvas.addEventListener("mousedown", (e) => {
        saveState();

        const x = e.offsetX;
        const y = e.offsetY;

        if (currentTool === "fill") {
            fillBucket(x, y);
            return;
        }

        drawing = true;
        lastX = x;
        lastY = y;
    });

    canvas.addEventListener("mouseup", () => {
        drawing = false;
        solidifyEdges();
    });

    canvas.addEventListener("mouseleave", () => {
        drawing = false;
        solidifyEdges();
    });

    canvas.addEventListener("mousemove", (e) => {
        if (!drawing) return;

        if (currentTool === "brush" || currentTool === "eraser") {
            drawStroke(e.offsetX, e.offsetY);
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

function colorsMatch(a, b, tolerance = 80) {
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

    // Get canvas pixel data
    const imageData = ctx.getImageData(0, 0, w, h);
    const data = imageData.data;

    // Convert currentColor into RGBA values
    ctx.fillStyle = currentColor;
    ctx.fillRect(0, 0, 0, 0);
    const fill = ctx.fillStyle;

    // Extract fill color
    const temp = document.createElement("canvas").getContext("2d");
    temp.fillStyle = fill;
    temp.fillRect(0, 0, 1, 1);
    const fillColor = temp.getImageData(0, 0, 1, 1).data;

    const startPos = (startY * w + startX) * 4;
    const targetColor = data.slice(startPos, startPos + 4);

    // If clicking on same color → no need to fill
    if (colorsMatch(fillColor, targetColor)) return;

    const queue = [];
    queue.push([startX, startY]);

    while (queue.length) {
        const [x, y] = queue.shift();
        let idx = (y * w + x) * 4;

        // Skip if not target color
        if (!colorsMatch(data.slice(idx, idx + 4), targetColor, 80)) continue;

        // Set pixel to fillColor
        data[idx] = fillColor[0];
        data[idx + 1] = fillColor[1];
        data[idx + 2] = fillColor[2];
        data[idx + 3] = 255;

        // Add neighbors
        if (x > 0) queue.push([x - 1, y]);
        if (x < w - 1) queue.push([x + 1, y]);
        if (y > 0) queue.push([x, y - 1]);
        if (y < h - 1) queue.push([x, y + 1]);
    }

    // Apply filled image back
    ctx.putImageData(imageData, 0, 0);
}