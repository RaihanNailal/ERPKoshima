/** @odoo-module **/

import { Component, useRef, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

export class ScurveChart extends Component {

    setup() {
        this.overlayCanvas = useRef("overlayCanvas");
        this.orm = useService("orm");
        this.actionService = useService("action");

        this.projectId =
            this.props.action?.params?.project_id ||
            this.props.action?.context?.active_id;

        this.state = useState({
            summary: [],
            weeks_header: [],
            tasks: [],
            total_weight: 0,
            current_week: 1,
            selected_week: null,
            selected_week_label: "Pilih Minggu",
        });

        this._resizeTimer = null;

        this._resizeHandler = () => {
            clearTimeout(this._resizeTimer);
            this._resizeTimer = setTimeout(()=>{
                this.drawOverlayLine();
            },120);
        };

        onMounted(async () => {
            await this.loadData();

            // 🔥 TAMBAHAN DI SINI (SETELAH loadData)
            this.currentWeekIndex = Math.max(
                0,
                (this.state.current_week || 1) - 1
            );

            window.addEventListener("resize", this._resizeHandler);

            // 🔥 draw sekali setelah render
            requestAnimationFrame(()=>{
                requestAnimationFrame(()=>{
                    this.drawOverlayLine();
                });
            });
        });
    }

    // =========================
    // LOAD DATA
    // =========================
    async loadData() {
        try {
            const result = await this.orm.call(
                "pm.project",
                "get_scurve_data",
                [this.projectId]
            );

            if (!result) return;

            // 🔥 WAJIB: assign satu-satu (jangan Object.assign)
            this.state.summary = result.summary || [];
            this.state.weeks_header = result.weeks_header || [];
            this.state.tasks = result.tasks || [];
            this.state.total_weight = result.total_weight || 0;

            this.state.current_week = result.current_week || 1;

            // kalau ada field lain, tambahin juga:
            this.state.project_name = result.project_name;
            this.state.vendor = result.vendor;
            this.state.po_number = result.po_number;
            this.state.logo_left = result.logo_left;
            this.state.logo_right = result.logo_right;
            this.state.project_start = result.project_start;
            this.state.project_end = result.project_end;
            this.state.remaining_days = result.remaining_days;

            this.state.sign_left_company = result.sign_left_company || "";
            this.state.sign_left_name = result.sign_left_name || "";
            this.state.sign_left_position = result.sign_left_position || "";
            this.state.sign_left_date = result.sign_left_date || "";

            this.state.sign_right_company = result.sign_right_company || "";
            this.state.sign_right_name = result.sign_right_name || "";
            this.state.sign_right_position = result.sign_right_position || "";

            // 🔥 DEFAULT SELECT WEEK
            if (this.state.current_week) {
                this.state.selected_week = this.state.weeks_header.find(
                    w => parseInt(w.num) === parseInt(this.state.current_week)
                );
                this.state.selected_week_label = `W${this.state.current_week}`;
            }
            console.log("SELECTED WEEK NUM:", this.state.selected_week?.num);

            // 🔥 EXISTING
            this.currentWeekIndex = (this.state.current_week || 1) - 1;

            if (this.currentWeekIndex === -1) {
                this.currentWeekIndex = 0;
            }

            console.log("SUMMARY DETAIL:", this.state.summary.map(s => ({
                plan: s.plan_cum,
                actual: s.actual_cum,
                deviation: s.deviation
            })));

            console.log("CURRENT WEEK:", this.state.current_week);
            console.log("SELECTED WEEK:", this.state.selected_week);

            console.log("TASKS:", result.tasks);
            console.log("SUMMARY:", result.summary);
            console.log("WEEKS:", result.weeks_header);

        } catch (error) {
            console.error("SCurve Load Error:", error);
        }
    }

    // =========================
    // DRAW OVERLAY
    // =========================
    drawOverlayLine() {
        const canvas = this.overlayCanvas.el;
        if (!canvas || !this.state.summary.length) return;

        const wrapper = canvas.closest(".table-wrapper");
        const table = wrapper?.querySelector("table");

        if (!wrapper || !table) return;

        const ctx = canvas.getContext("2d");
        ctx.setTransform(1,0,0,1,0,0);

        const wrapperRect =
            wrapper.getBoundingClientRect();

        const tableRect =
            table.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;

        // FULL LEBAR TABEL DINAMIS (31,53,100 minggu aman)
        const fullWidth = table.scrollWidth + 100;

        canvas.width = fullWidth * dpr;
        canvas.height = table.scrollHeight * dpr;

        canvas.style.width = fullWidth + "px";
        canvas.style.height = table.scrollHeight + "px";

        ctx.scale(dpr, dpr);
        ctx.clearRect(
            0,
            0,
            fullWidth,
            table.scrollHeight
        );
        
        const rows = table.querySelectorAll("tbody tr");
        if (!rows.length) return;

        const top =
            rows[0].getBoundingClientRect().top
            - tableRect.top;

        const bottom =
            rows[rows.length - 1].getBoundingClientRect().bottom
            - tableRect.top;
        const height = bottom - top;

        const footerRows = table.querySelectorAll("tfoot tr");
        if (footerRows.length < 5) return;

        const allTargetCells = footerRows[2].querySelectorAll("td");

        const startIndex = 2;

        const targetCells = Array.from(allTargetCells).slice(
            startIndex,
            startIndex + this.state.summary.length
        );

        const limit = this.state.selected_week
            ? (typeof this.state.selected_week === "number"
                ? this.state.selected_week
                : this.state.selected_week.num)
            : this.currentWeekIndex + 1;

        // 🔥 SCHEDULE = FULL
        const scheduleSummary = this.state.summary.filter(
            s => s.plan_cum != null
        );

        // 🔥 ACTUAL = IKUT DROPDOWN
        const actualSummary = this.state.summary
            .slice(0, limit)
            .filter(s => s.actual_cum != null);

        const planPoints = [];
        const actualPoints = [];

        // =========================
        // 🔥 SCHEDULE (FULL)
        // =========================
        scheduleSummary.forEach((s, i) => {
            const cell = targetCells[i];
            if (!cell) return;

            const cellRect = cell.getBoundingClientRect();
            const x =
                cellRect.left
                - tableRect.left
                + cellRect.width / 2;

            const yPlan = bottom - (s.plan_cum / 100) * height;

            planPoints.push({ x, y: yPlan });
        });

        // =========================
        // 🔥 ACTUAL (LIMITED)
        // =========================
        actualSummary.forEach((s, i) => {
            const cell = targetCells[i];
            if (!cell) return;

            const cellRect = cell.getBoundingClientRect();
            const x =
                cellRect.left
                - tableRect.left
                + cellRect.width / 2;

            const yAct = bottom - (s.actual_cum / 100) * height;

            actualPoints.push({ x, y: yAct });
        });

        // 🔥 SCHEDULE FULL
        this.drawPath(
            ctx,
            planPoints,
            "#22c55e",
            scheduleSummary.map(s => s.plan_cum || 0)
        );

        // 🔥 ACTUAL TERBATAS
        this.drawPath(
            ctx,
            actualPoints,
            "#f59e0b",
            actualSummary.map(s => s.actual_cum || 0)
        );
    }

    // =========================
    // DRAW PATH + LABEL
    // =========================
    drawPath(ctx, points, color, values = []) {

        if (!points.length) return;

        // =========================
        // 🔥 DRAW LINE (kalau >1 titik)
        // =========================
        if (points.length > 1) {
            ctx.beginPath();
            ctx.strokeStyle = color;
            ctx.lineWidth = 3;

            ctx.moveTo(points[0].x, points[0].y);

            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(points[i].x, points[i].y);
            }

            ctx.stroke();
        }

        // =========================
        // 🔥 DRAW TITIK + LABEL (SELALU)
        // =========================
        points.forEach((p, i) => {

            const val = values[i];

            if (val == null) return;

            // titik
            ctx.beginPath();
            ctx.arc(p.x, p.y, 4, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();

            // label
            const text = val.toFixed(1) + "%";

            ctx.font = "11px Arial";
            const textWidth = ctx.measureText(text).width;

            const padding = 4;
            const boxWidth = textWidth + padding * 2;
            const boxHeight = 16;

            const boxX = p.x - boxWidth / 2;

            const boxY = p.y + 10;

            ctx.fillStyle = color;
            ctx.fillRect(boxX, boxY, boxWidth, boxHeight);

            ctx.fillStyle = "#fff";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(text, p.x, boxY + boxHeight / 2);
        });
    }

    // =========================
    // DROPDOWN
    // =========================
    selectWeek(week) {
        this.state.selected_week = week;
        this.state.selected_week_label = `W${week.num}`;

        setTimeout(() => this.drawOverlayLine(), 50);
    }

    formatWeekRange(date) {
        const start = new Date(date);
        const end = new Date(date);

        // default +6 hari
        end.setDate(end.getDate() + 6);

        // 🔥 BATASI DENGAN PROJECT END
        if (this.state.project_end) {
            const projectEnd = new Date(this.state.project_end);

            if (end > projectEnd) {
                end.setTime(projectEnd.getTime());
            }
        }

        return `${start.toLocaleDateString("id-ID")} - ${end.toLocaleDateString("id-ID")}`;
    }

    formatNum(val) {
        if (val === null || val === undefined) return "-";
        const num = Number(val);
        if (isNaN(num)) return "-";
        return num.toFixed(2);
    }

    async updateSignature(field, ev) {
        const value = ev.target.value;

        try {
            await this.orm.call(
                "pm.project",
                "write_signature",
                [this.projectId, field, value]
            );
        } catch (err) {
            console.error("SAVE ERROR:", err);
        }
    }

    async exportPDF() {

        try {

            const selectedWeek =
                this.state.selected_week?.num
                || this.state.current_week
                || 1;

            console.log(
                "Export week:",
                selectedWeek
            );

            window.open(
                `/pm_scurve/export_reportlab/${this.projectId}?week=${selectedWeek}`,
                "_blank"
            );

        } catch(e){
            console.error(
                "EXPORT ERROR:",
                e
            );
        }
    }
}

ScurveChart.template = "pm_scurve.ScurveChart";

registry.category("actions").add(
    "pm_scurve.scurve_js_action",
    ScurveChart
);