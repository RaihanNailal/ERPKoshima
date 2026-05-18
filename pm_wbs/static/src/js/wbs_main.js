/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class WBSMain extends Component {

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            projects: [],
            users: [],
            selectedProject: null,
            weeks: [],
            tasks: [],
            summary: [],
            total_weight: 0,
            total_progress: 0,
        });

        // 🔥 debounce reload
        this._reloadTimer = null;

        onMounted(async () => {
            await this.loadProjects();
            await this.loadUsers();
        });
    }

    // =========================
    // SAFE RELOAD (ANTI SPAM)
    // =========================
    safeReload() {
        clearTimeout(this._reloadTimer);
        this._reloadTimer = setTimeout(() => {
            this.reloadData();
        }, 300);
    }

    // =========================
    // LOAD DATA
    // =========================

    async loadProjects() {
        this.state.projects = await this.orm.searchRead(
            "pm.project", [], ["name"]
        );
    }

    async loadUsers() {
        this.state.users = await this.orm.searchRead(
            "res.users", [], ["name"]
        );
    }

    // =========================
    // SELECT PROJECT
    // =========================

    async selectProject(ev) {
        const projectId = parseInt(ev.target.value);
        if (!projectId) return;

        this.state.selectedProject = projectId;
        await this.reloadData();
    }

    // =========================
    // CRUD TASK
    // =========================

    async addTask() {
        if (!this.state.selectedProject) return;

        const today = new Date().toISOString().split('T')[0];

        await this.orm.create("pm.task", [{
            name: "New Task",
            project_id: this.state.selectedProject,
            manual_start_date: false,
            manual_end_date: false,
            progress: 0,
            weight: 0
        }]);

        this.safeReload();
    }

    async addSubTask(ev) {
        const parentId = parseInt(ev.target.dataset.id);
        if (!parentId) return;

        const today = new Date().toISOString().split('T')[0];

        await this.orm.create("pm.task", [{
            name: "Sub Task",
            project_id: this.state.selectedProject,
            parent_id: parentId,
            manual_start_date: false,
            manual_end_date: false,
            progress: 0,
            weight: 0
        }]);

        this.safeReload();
    }

    async deleteTask(ev) {
        const taskId = parseInt(ev.target.dataset.id);
        if (!taskId) return;

        if (!confirm("Yakin hapus task?")) return;

        await this.orm.unlink("pm.task", [taskId]);
        this.safeReload();
    }

    // =========================
    // UPDATE BASIC FIELD
    // =========================

    async updateTaskName(ev) {
        const taskId = parseInt(ev.target.dataset.id);

        await this.orm.write("pm.task", [taskId], {
            name: ev.target.value
        });

        this.safeReload();
    }

    async updateWeight(ev) {
        const taskId = parseInt(ev.target.dataset.id);
        let value = parseFloat(ev.target.value);

        if (isNaN(value)) value = 0;
        value = Math.max(0, Math.min(100, value));

        await this.orm.write("pm.task", [taskId], {
            weight: value
        });

        this.safeReload();
    }

    // =========================
    // 🔥 WEEKLY (UNIFIED)
    // =========================

    async updateWeekly(ev, type) {
        const taskId = parseInt(ev.target.dataset.task);
        const week = ev.target.dataset.week;
        let value = parseFloat(ev.target.value) || 0;

        const task = this.state.tasks.find(t => t.id === taskId);

        let total = 0;

        for (const w of task.weeks) {
            if (w.date === week) {
                total += value;
            } else {
                total += w[type] || 0;
            }
        }

        if (total > task.weight) {
            alert(`Total ${type.toUpperCase()} melebihi bobot task!`);
            return;
        }

        await this.orm.call(
            "pm.wbs.task.week",
            type === 'plan' ? "write_plan" : "write_actual",
            [taskId, week, value]
        );

        this.safeReload();
    }

    updatePlanWBS(ev) {
        return this.updateWeekly(ev, 'plan');
    }

    updateActualWBS(ev) {
        return this.updateWeekly(ev, 'actual');
    }

    // =========================
    // RELOAD DATA
    // =========================

    async reloadData() {
        if (!this.state.selectedProject) return;

        const data = await this.orm.call(
            "pm.project",
            "get_wbs_data",
            [this.state.selectedProject]
        );

        this.state.weeks = data.weeks || [];
        this.state.tasks = (data.tasks || []).map(t => ({
            ...t,
            pic_id: t.has_child ? false : t.pic_id,
            pic_name: t.pic || "",
        }));
        this.state.summary = data.summary || [];
        this.state.total_weight = data.total_weight || 0;
        this.state.total_progress = data.total_progress || 0;
    }

    async updatePIC(ev) {
        const taskId = parseInt(ev.target.dataset.id);
        const userId = parseInt(ev.target.value);

        const task = this.state.tasks.find(t => t.id === taskId);

        if (task.has_child) {
            alert("Engineer hanya boleh diisi pada subtask");
            return;
        }

        await this.orm.write("pm.task", [taskId], {
            pic_id: userId || false
        });

        this.safeReload();
    }

    formatNumber(val) {
        if (!val) return 0;
        return Number.isInteger(val) ? val : parseFloat(val.toFixed(2));
    }

    openTask(taskId) {
        this.action.doAction({
            type:'ir.actions.act_window',
            res_model:'pm.task',
            res_id:taskId,

            views:[[false,'form']],

            target:'new',

            context:{
                form_view_ref:'pm_issue.view_pm_task_form_engineer',
                form_view_initial_mode:'view',
                edit:false,
                create:false,
                delete:false
            }
        });
    }

    async updateStartDate(ev) {
        const id = parseInt(ev.target.dataset.id);
        const value = ev.target.value;

        await this.orm.write('pm.task', [id], {
            manual_start_date: value,
        });

        this.safeReload();
    }

    async updateEndDate(ev) {
        const id = parseInt(ev.target.dataset.id);
        const value = ev.target.value;

        await this.orm.write('pm.task', [id], {
            manual_end_date: value,
        });

        this.safeReload();
    }

    async exportExcel() {
        if (!this.state.selectedProject) return;

        const action = await this.orm.call(
            "pm.project",
            "action_export_wbs_excel",
            [this.state.selectedProject]
        );

        this.action.doAction(action);
    }

    async printPDF() {
        if (!this.state.selectedProject) return;

        await this.action.doAction({
            type: 'ir.actions.report',
            report_type: 'qweb-pdf',
            report_name: 'pm_wbs.report_wbs_template',

            context: {
                active_model: 'pm.project',
                active_id: this.state.selectedProject,
                active_ids: [this.state.selectedProject],
            }
        });
    }

}

WBSMain.template = "pm_wbs.WBSMainTemplate";