// Interactive Virtual Fence Drawing Library
class FenceDrawer {
    constructor(canvasId, imageId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.points = []; // [{x_norm, y_norm}, ...]
        this.initCanvas();
    }

    initCanvas() {
        this.canvas.addEventListener('click', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const normX = x / this.canvas.width;
            const normY = y / this.canvas.height;
            
            this.points.push([parseFloat(normX.toFixed(3)), parseFloat(normY.toFixed(3))]);
            this.redraw();
        });
    }

    clear() {
        this.points = [];
        this.redraw();
    }

    redraw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        if (this.points.length === 0) return;

        const w = this.canvas.width;
        const h = this.canvas.height;

        // Draw points
        this.ctx.fillStyle = '#00ff88';
        this.ctx.strokeStyle = '#00ff88';
        this.ctx.lineWidth = 2;

        this.ctx.beginPath();
        this.points.forEach((pt, idx) => {
            const px = pt[0] * w;
            const py = pt[1] * h;
            
            if (idx === 0) {
                this.ctx.moveTo(px, py);
            } else {
                this.ctx.lineTo(px, py);
            }
            
            this.ctx.arc(px, py, 4, 0, 2 * Math.PI);
        });

        if (this.points.length > 2) {
            this.ctx.closePath();
            this.ctx.fillStyle = 'rgba(0, 255, 136, 0.2)';
            this.ctx.fill();
        }

        this.ctx.stroke();
    }

    getCoordinates() {
        return this.points;
    }
}
