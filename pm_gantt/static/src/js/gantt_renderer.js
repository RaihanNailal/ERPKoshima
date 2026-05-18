/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useEffect, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { loadJS, loadCSS } from "@web/core/assets";
import { onWillUnmount } from "@odoo/owl";

export class GanttClientAction extends Component {

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.ganttRef = useRef("ganttContainer");
        this.gantt = null;

        this.projectId = this.props.action.context?.project_id;

        console.log("ACTION:", this.props.action);

        this.state = useState({
            hasData: false,
            error: false,
        });

        this.tasks = [];

        this.display = {
            controlPanel: { "top-right": false, "bottom-right": false },
        };

        onWillStart(async () => {
            await Promise.all([
                loadCSS("/pm_gantt/static/src/lib/frappe-gantt.css"),
                loadJS("/pm_gantt/static/src/lib/frappe-gantt.min.js"),
            ]);

            if (this.projectId) {
                await this.fetchData();
            }
        });

        useEffect(() => {
            if (this.state.hasData && this.ganttRef.el) {
                this.renderGantt();
            }

            if (this.state.error && this.ganttRef.el) {
                this.showError("Gagal memuat data timeline.");
            }

            if (!this.state.hasData && !this.state.error && this.ganttRef.el) {
                this.showEmpty();
            }

        }, () => [this.state.hasData, this.state.error]);
    }

    // =========================
    // FETCH DATA
    // =========================
    async fetchData() {
        try {
            const response = await fetch(`/pm_gantt/get_data/${this.projectId}`)
                .catch(() => null);

            if (!response || !response.ok) {
                this.state.error = true;
                return;
            }

            const data = await response.json();

            this.tasks = data.map(task => ({
                ...task,
                progress: Number(task.progress) || 0,
                pic: task.pic || "-",
            }));

            console.log("GANTT TASKS:", this.tasks);
            this.state.hasData = this.tasks.length > 0;

        } catch (error) {
            console.error("Gantt Fetch Error:", error);
            this.state.error = true;
        }
    }

    // =========================
    // RENDER GANTT
    // =========================
    renderGantt() {
        if (!this.ganttRef.el) return;

        this.ganttRef.el.innerHTML = "";

        const wrapper = document.createElement("div");
        wrapper.className = "gantt-wrapper gantt";

        const sidebar = document.createElement("div");
        sidebar.className = "gantt-sidebar";

        const chartContainer = document.createElement("div");
        chartContainer.className = "gantt-chart";

        wrapper.appendChild(sidebar);
        wrapper.appendChild(chartContainer);
        this.ganttRef.el.appendChild(wrapper);

        try {
            this.gantt = new Gantt(chartContainer, this.tasks, {
                header_height: 50,
                column_width: 40,
                step: 24,
                view_modes: ["Day", "Week", "Month"],
                bar_height: 25,
                padding: 18,
                view_mode: "Day",
                date_format: "YYYY-MM-DD",
                readonly: true,
                popup_on: "mousemove", 
                custom_popup_html: (task) => {
                    return `
                        <div style="
                            min-width:180px;
                            max-width:220px;
                            padding:10px 12px;
                            line-height:1.4;
                            color:#fff;
                            font-size:12px;
                        ">

                            <div style="
                                font-weight:600;
                                font-size:13px;
                                margin-bottom:6px;
                            ">
                                ${task.name}
                            </div>

                            <div style="display:flex; justify-content:space-between;">
                                <span>Weight</span>
                                <b>${task.weight || 0}%</b>
                            </div>

                            <div style="display:flex; justify-content:space-between;">
                                <span>Progress</span>
                                <b>${task.actual || 0}%</b>
                            </div>

                            <div style="display:flex; justify-content:space-between;">
                                <span>Sisa</span>
                                <b>${task.sisa || 0}%</b>
                            </div>

                            <div style="
                                margin-top:6px;
                                border-top:1px solid rgba(255,255,255,0.2);
                                padding-top:4px;
                                display:flex;
                                justify-content:space-between;
                            ">
                                <span>PIC</span>
                                <b>${task.pic || "-"}</b>
                            </div>

                        </div>
                    `;
                }
            });

            window.requestAnimationFrame(() => {

                // Auto fit label ke panjang bar
                document.querySelectorAll(".bar-wrapper").forEach(bar=>{

                    const rect = bar.querySelector(".bar");
                    const label = bar.querySelector(".bar-label");

                    if(!rect || !label) return;

                    const fullText = label.textContent.trim();
                    
                    bar.setAttribute(
                    "title",
                    fullText
                    );

                    const barWidth = parseFloat(
                        rect.getAttribute("width")
                    );

                    // estimasi karakter yang muat
                    const charsFit = Math.floor(barWidth / 6.5);

                    if (barWidth < 55){
                        label.textContent = ""; // terlalu kecil hide
                    }
                    else if(fullText.length > charsFit){
                        label.textContent =
                        fullText.substring(
                            0,
                            Math.max(charsFit-3,4)
                        ) + "...";
                    }

                    // font menyesuaikan
                    if(barWidth < 90){
                        label.setAttribute(
                        "font-size",
                        "8"
                        );
                    }
                    else{
                        label.setAttribute(
                        "font-size",
                        "10"
                        );
                    }

                    // center label di bar
                    const x = parseFloat(
                        rect.getAttribute("x")
                    );

                    label.setAttribute(
                        "x",
                        x + (barWidth/2)
                    );

                    label.setAttribute(
                        "text-anchor",
                        "middle"
                    );
                });

                document.querySelectorAll(".bar-wrapper").forEach(bar=>{

                    let hoverTimer;

                    bar.addEventListener("mouseenter",()=>{

                        hoverTimer=setTimeout(()=>{

                            const popup=
                                document.querySelector(
                                    ".popup-wrapper"
                                );

                            if(popup){
                                popup.classList.add("active");
                            }

                        },500);

                    });

                    bar.addEventListener("mouseleave",()=>{

                        clearTimeout(hoverTimer);

                        const popup=
                            document.querySelector(
                                ".popup-wrapper"
                            );

                        if(popup){
                            popup.classList.remove("active");
                        }

                    });

                });

                this.renderSidebar(
                sidebar,
                chartContainer
                );

            });

            chartContainer.addEventListener("scroll", () => {
                sidebar.scrollTop = chartContainer.scrollTop;
            });

        } catch (e) {
            console.error("Gantt Init Error:", e);
            this.showError("Gagal render Gantt.");
        }
    }

    // =========================
    // SIDEBAR RENDER
    // =========================
    renderSidebar(sidebar, chartContainer) {

        const firstGridRow = chartContainer.querySelector(".grid-row");

        const rowHeight = firstGridRow
            ? firstGridRow.getBBox().height
            : 45;

        const header = document.createElement("div");
        header.className = "gantt-sidebar-header";
        header.style.height = "61px";

        header.innerHTML = `
            <div class="gantt-col-wbs">WBS</div>
            <div class="gantt-col-name">TASK NAME</div>
            <div class="gantt-col-date">START</div>
            <div class="gantt-col-date">FINISH</div>
            <div class="gantt-col-duration">DUR</div>
        `;

        sidebar.appendChild(header);

        this.tasks.forEach(task => {

            const row = document.createElement("div");
            row.className = "gantt-sidebar-row";

            row.style.height = rowHeight + "px";
            row.style.lineHeight = rowHeight + "px";

            // ✅ DECLARE DULU
            const indent = task.level * 16;

            const formatDate = (d) => {
                if (!d) return "-";
                const date = new Date(d);
                return date.toLocaleDateString("en-GB"); // 15/04/2026
            };

            row.innerHTML = `
                <div class="gantt-col-wbs">
                    ${task.wbs}
                </div>

                <div class="gantt-col-name" 
                    title="${task.name}" 
                    style="padding-left:${indent}px">
                    ${task.name}
                </div>

                <div class="gantt-col-date">
                    ${formatDate(task.start)}
                </div>

                <div class="gantt-col-date">
                    ${formatDate(task.end)}
                </div>

                <div class="gantt-col-duration">
                    ${task.duration}d
                </div>
            `;

            if (task.has_child) {
                row.classList.add("parent");
            }

            sidebar.appendChild(row);
        });

        console.log("HEADER HTML:", header.innerHTML);
    }

    // =========================
    // UI STATES
    // =========================
    showEmpty() {
        this.ganttRef.el.innerHTML =
            "<p class='text-center p-5'>Data tugas kosong atau tanggal belum diisi.</p>";
    }

    showError(message) {
        this.ganttRef.el.innerHTML =
            `<p class='text-center p-5 text-danger'>${message}</p>`;
    }

    exportExcel() {
        const projectId = this.props.action.context.project_id;
        if (!projectId) return;

        window.open(`/pm_gantt/export_excel/${projectId}`, '_blank');
    }

    exportPDF() {
        const projectId = this.props.action.context.project_id;
        if (!projectId) return;

        window.open(`/pm_gantt/export_pdf/${projectId}`, '_blank');
    }
}

GanttClientAction.template = "pm_gantt.GanttView";
GanttClientAction.components = { Layout };

registry.category("actions").add(
    "pm_gantt.gantt_js_action",
    GanttClientAction
);