/** @odoo-module **/

import { registry } from "@web/core/registry";

import {
    Component,
    useState,
    onWillStart,
} from "@odoo/owl";

import { ScurveChart } from "@pm_scurve/js/scurve_chart";

import { useService } from "@web/core/utils/hooks";

export class WeeklyReport extends Component {

    static template =
        "pm_report.WeeklyReport";

    static components = {
        ScurveChart,
    };

    setup() {

        this.orm =
            useService("orm");

        this.action = useService("action");

        this.projectId =
            this.props.action.params.project_id || false;

        this.state = useState({

            loading: true,

            project: {},

            tables: [],

            safetyActivities: [],

            issues: [],

            generalWorks: [],

            overview: [],

            activitySchedules: [],

            photos: [],

            timeline: {},

            today: new Date(),

            current_week: 1,

            period_start: null,

            period_end: null,

            showScurve: false,

            selectedProjectId: null,
        });

        onWillStart(async () => {

            if (!this.projectId) {
                return;
            }

            await this.loadProject();

            await Promise.all([
                this.reloadTables(),
                this.reloadSafetyActivities(),
                this.reloadIssues(),
                this.reloadGeneralWorks(),
                this.reloadOverview(),
                this.reloadActivitySchedules(),
                this.reloadTimeline(),
                this.reloadPhotos(),
            ]);

            this.calculatePeriod();

            this.state.loading = false;
        });
    }

    // =========================================================
    // LOAD PROJECT
    // =========================================================

    async loadProject() {

        const result =
            await this.orm.read(
                "pm.project",
                [this.projectId],
                [
                    "name",
                    "vendor",
                    "po_number",
                    "project_location",
                    "start_date",
                    "end_date",
                    "logo_left",
                    "logo_right",
                    "client_id",

                    "prepared_by",
                    "acknowledged_by",
                    "checked_by",
                    "approved_by",

                    "prepared_company",
                    "acknowledged_company",
                    "checked_company",
                    "approved_company",

                    "last_week",
                    "this_week",
                    "accumulative",

                    "mcu_process",
                    "input_berkas",
                    "induction_process",
                    "id_card_process",
                    "id_card",
                    "waskat",
                    "manpower_note",
                ]
            );

        this.state.project =
            result.length
                ? result[0]
                : {};
    }

    // =========================================================
    // DATE
    // =========================================================

    calculatePeriod() {

        if (!this.state.project.start_date) {
            return;
        }

        const startDate =
            new Date(
                this.state.project.start_date
            );

        const today =
            new Date();

        const diff =
            today - startDate;

        const days =
            Math.floor(
                diff / (
                    1000 * 60 * 60 * 24
                )
            );

        let week =
            Math.floor(days / 7) + 1;

        if (week < 1) {
            week = 1;
        }

        this.state.current_week =
            week;

        const periodStart =
            new Date(startDate);

        periodStart.setDate(
            startDate.getDate() +
            ((week - 1) * 7)
        );

        const periodEnd =
            new Date(periodStart);

        periodEnd.setDate(
            periodStart.getDate() + 6
        );

        this.state.period_start =
            periodStart;

        this.state.period_end =
            periodEnd;
    }

    formatDate(dateStr) {

        if (!dateStr) {
            return "";
        }

        return new Date(dateStr)
            .toLocaleDateString(
                "id-ID",
                {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                }
            );
    }

    // =========================================================
    // HELPERS
    // =========================================================

    getTable(tableId) {

        return this.state.tables.find(
            t => t.id === tableId
        );
    }

    getLine(lineId) {

        for (const table of this.state.tables) {

            const line =
                table.lines.find(
                    l => l.id === lineId
                );

            if (line) {
                return line;
            }
        }

        return null;
    }

    getSchedule(category) {

        return this.state.activitySchedules.find(
            s => s.category === category
        );
    }

    // =========================================================
    // PROJECT FIELD
    // =========================================================

    async updateField(field, ev) {

        if (!this.projectId) {
            return;
        }

        const value =
            ev.target.value;

        await this.orm.write(
            "pm.project",
            [this.projectId],
            {
                [field]: value,
            }
        );

        this.state.project[field] =
            value;
    }

    // =========================================================
    // TABLES
    // =========================================================

    async reloadTables() {

        const tables =
            await this.orm.searchRead(
                "pm.weekly.table",
                [
                    ["project_id", "=", this.projectId]
                ],
                [
                    "id",
                    "name",
                    "type",
                ]
            );

        const tableIds =
            tables.map(t => t.id);

        const columns =
            tableIds.length
                ? await this.orm.searchRead(
                    "pm.weekly.table.column",
                    [
                        ["table_id", "in", tableIds]
                    ],
                    [
                        "id",
                        "name",
                        "table_id",
                    ]
                )
                : [];

        const lines =
            tableIds.length
                ? await this.orm.searchRead(
                    "pm.weekly.table.line",
                    [
                        ["table_id", "in", tableIds]
                    ],
                    [
                        "id",
                        "name",
                        "position",
                        "note",
                        "table_id",
                    ]
                )
                : [];

        const lineIds =
            lines.map(l => l.id);

        const values =
            lineIds.length
                ? await this.orm.searchRead(
                    "pm.weekly.table.value",
                    [
                        ["line_id", "in", lineIds]
                    ],
                    [
                        "id",
                        "line_id",
                        "column_id",
                        "value",
                    ]
                )
                : [];

        const valueMap = {};

        values.forEach(val => {

            const lineId =
                val.line_id[0];

            if (!valueMap[lineId]) {
                valueMap[lineId] = {};
            }

            valueMap[lineId][
                val.column_id[0]
            ] = val.value;
        });

        tables.forEach(table => {

            table.columns =
                columns.filter(
                    c =>
                        c.table_id[0]
                        === table.id
                );

            table.lines =
                lines
                    .filter(
                        l =>
                            l.table_id[0]
                            === table.id
                    )
                    .map(line => ({
                        ...line,
                        values:
                            valueMap[line.id] || {},
                    }));
        });

        this.state.tables =
            tables;
    }

    async addTable() {

        const ids =
            await this.orm.create(
                "pm.weekly.table",
                [{
                    project_id: this.projectId,
                    name: "New Section",
                }]
            );

        this.state.tables.push({

            id: ids[0],

            name: "New Section",

            columns: [],

            lines: [],
        });
    }

    async deleteTable(ev) {

        const tableId =
            parseInt(
                ev.currentTarget.dataset.tableId
            );

        await this.orm.unlink(
            "pm.weekly.table",
            [tableId]
        );

        this.state.tables =
            this.state.tables.filter(
                t => t.id !== tableId
            );
    }

    async updateTable(tableId, field, ev) {

        const value =
            ev.target.value;

        await this.orm.write(
            "pm.weekly.table",
            [tableId],
            {
                [field]: value,
            }
        );

        const table =
            this.getTable(tableId);

        if (table) {
            table[field] = value;
        }
    }

    // =========================================================
    // ROW
    // =========================================================

    async addRow(ev) {

        const tableId =
            parseInt(
                ev.currentTarget.dataset.tableId
            );

        const ids =
            await this.orm.create(
                "pm.weekly.table.line",
                [{
                    table_id: tableId,
                    name: "",
                }]
            );

        const table =
            this.getTable(tableId);

        if (!table) {
            return;
        }

        table.lines.push({

            id: ids[0],

            name: "",

            position: "",

            note: "",

            values: {},
        });
    }

    async updateLine(lineId, field, ev) {

        const value =
            ev.target.value;

        await this.orm.write(
            "pm.weekly.table.line",
            [lineId],
            {
                [field]: value,
            }
        );

        const line =
            this.getLine(lineId);

        if (line) {
            line[field] = value;
        }
    }

    // =========================================================
    // COLUMN
    // =========================================================

    async addColumn(ev) {

        const tableId =
            parseInt(
                ev.currentTarget.dataset.tableId
            );

        const ids =
            await this.orm.create(
                "pm.weekly.table.column",
                [{
                    table_id: tableId,
                    name: "Competency",
                }]
            );

        const table =
            this.getTable(tableId);

        if (!table) {
            return;
        }

        table.columns.push({

            id: ids[0],

            name: "Competency",
        });
    }

    async updateColumn(columnId, ev) {

        const value =
            ev.target.value;

        await this.orm.write(
            "pm.weekly.table.column",
            [columnId],
            {
                name: value,
            }
        );

        this.state.tables.forEach(table => {

            const column =
                table.columns.find(
                    c => c.id === columnId
                );

            if (column) {
                column.name = value;
            }
        });
    }

    // =========================================================
    // VALUE
    // =========================================================

    async toggleValue(lineId, columnId, ev) {

        const checked =
            ev.target.checked;

        const existing =
            await this.orm.searchRead(
                "pm.weekly.table.value",
                [
                    ["line_id", "=", lineId],
                    ["column_id", "=", columnId]
                ],
                ["id"]
            );

        let valueId = null;

        if (existing.length) {

            valueId =
                existing[0].id;

            await this.orm.write(
                "pm.weekly.table.value",
                [valueId],
                {
                    value: checked,
                }
            );

        } else {

            await this.orm.create(
                "pm.weekly.table.value",
                [{
                    line_id: lineId,
                    column_id: columnId,
                    value: checked,
                }]
            );
        }

        const line =
            this.getLine(lineId);

        if (!line) {
            return;
        }

        line.values[columnId] =
            checked;
    }

    // =========================================================
    // SAFETY ACTIVITY
    // =========================================================

    async reloadSafetyActivities() {

        const activities =
            await this.orm.searchRead(
                "pm.safety.activity",
                [
                    ["project_id", "=", this.projectId]
                ],
                [
                    "id",
                    "name",
                ]
            );

        const activityIds =
            activities.map(a => a.id);

        const lines =
            activityIds.length
                ? await this.orm.searchRead(
                    "pm.safety.activity.line",
                    [
                        ["activity_id", "in", activityIds]
                    ],
                    [
                        "id",
                        "name",
                        "activity_id",
                    ]
                )
                : [];

        activities.forEach(activity => {

            activity.lines =
                lines.filter(
                    l =>
                        l.activity_id[0]
                        === activity.id
                );
        });

        this.state.safetyActivities =
            activities;
    }

    async addSafetyActivity() {

        const ids =
            await this.orm.create(
                "pm.safety.activity",
                [{
                    project_id: this.projectId,
                    name: "New Activity",
                }]
            );

        this.state.safetyActivities.push({

            id: ids[0],

            name: "New Activity",

            lines: [],
        });
    }

    async addSafetyBullet(ev) {

        const activityId =
            parseInt(
                ev.currentTarget.dataset.activityId
            );

        const ids =
            await this.orm.create(
                "pm.safety.activity.line",
                [{
                    activity_id: activityId,
                    name: "New Bullet",
                }]
            );

        const activity =
            this.state.safetyActivities.find(
                a => a.id === activityId
            );

        if (!activity) {
            return;
        }

        activity.lines.push({

            id: ids[0],

            name: "New Bullet",
        });
    }

    async updateSafetyActivity(activityId, ev) {

        const value =
            ev.target.value;

        await this.orm.write(
            "pm.safety.activity",
            [activityId],
            {
                name: value,
            }
        );

        const activity =
            this.state.safetyActivities.find(
                a => a.id === activityId
            );

        if (activity) {
            activity.name = value;
        }
    }

    async updateSafetyBullet(lineId, ev) {

        const value =
            ev.target.value;

        await this.orm.write(
            "pm.safety.activity.line",
            [lineId],
            {
                name: value,
            }
        );

        this.state.safetyActivities.forEach(activity => {

            const line =
                activity.lines.find(
                    l => l.id === lineId
                );

            if (line) {
                line.name = value;
            }
        });
    }

    async deleteSafetyActivity(ev) {

        const activityId = parseInt(
            ev.currentTarget.dataset.activityId
        );

        await this.orm.unlink(
            "pm.safety.activity",
            [activityId]
        );

        this.state.safetyActivities =
            this.state.safetyActivities.filter(
                activity => activity.id !== activityId
            );
    }

    // =========================================================
    // ISSUES
    // =========================================================

    async reloadIssues() {

        const issues =
            await this.orm.searchRead(
                "pm.issue",
                [
                    ["project_id", "=", this.projectId],
                    ["is_client_visible", "=", true],
                ],
                [
                    "register_number",
                    "name",
                    "submitted_by",
                    "submitted_date",
                    "reviewed_by",
                    "reviewed_date",
                    "status",
                ]
            );

        this.state.issues =
            issues;
    }

    // =========================================================
    // GENERAL WORK
    // =========================================================

    async reloadGeneralWorks() {

        const works =
            await this.orm.searchRead(
                "pm.general.work",
                [
                    ["project_id", "=", this.projectId]
                ],
                [
                    "id",
                    "name",
                ]
            );

        const workIds =
            works.map(w => w.id);

        const lines =
            workIds.length
                ? await this.orm.searchRead(
                    "pm.general.work.line",
                    [
                        ["work_id", "in", workIds]
                    ],
                    [
                        "id",
                        "name",
                        "work_id",
                    ]
                )
                : [];

        works.forEach(work => {

            work.lines =
                lines.filter(
                    l =>
                        l.work_id[0]
                        === work.id
                );
        });

        this.state.generalWorks =
            works;
    }

    async addGeneralWork() {

        const ids =
            await this.orm.create(
                "pm.general.work",
                [{
                    project_id: this.projectId,
                    name: "New Work",
                }]
            );

        this.state.generalWorks.push({

            id: ids[0],

            name: "New Work",

            lines: [],
        });
    }

    async addGeneralWorkBullet(ev) {

        const workId =
            parseInt(
                ev.currentTarget.dataset.workId
            );

        const ids =
            await this.orm.create(
                "pm.general.work.line",
                [{
                    work_id: workId,
                    name: "New Bullet",
                }]
            );

        const work =
            this.state.generalWorks.find(
                w => w.id === workId
            );

        if (!work) {
            return;
        }

        work.lines.push({

            id: ids[0],

            name: "New Bullet",
        });
    }

    async updateGeneralWork(workId, ev) {

        const value =
            ev.target.value;

        await this.orm.write(
            "pm.general.work",
            [workId],
            {
                name: value,
            }
        );

        const work =
            this.state.generalWorks.find(
                w => w.id === workId
            );

        if (work) {
            work.name = value;
        }
    }

    async updateGeneralWorkBullet(lineId, ev) {

        const value =
            ev.target.value;

        await this.orm.write(
            "pm.general.work.line",
            [lineId],
            {
                name: value,
            }
        );

        this.state.generalWorks.forEach(work => {

            const line =
                work.lines.find(
                    l => l.id === lineId
                );

            if (line) {
                line.name = value;
            }
        });
    }

    async deleteGeneralWork(ev) {

        const workId =
            parseInt(
                ev.currentTarget.dataset.workId
            );

        await this.orm.unlink(
            "pm.general.work",
            [workId]
        );

        this.state.generalWorks =
            this.state.generalWorks.filter(
                work => work.id !== workId
            );
    }

    // =========================================================
    // OVERVIEW
    // =========================================================

    async reloadOverview() {

        const overview =
            await this.orm.call(
                "pm.project",
                "get_weekly_overview",
                [this.projectId]
            );

        this.state.overview =
            overview || [];
    }

    // =========================================================
    // ACTIVITY SCHEDULE
    // =========================================================

    async reloadActivitySchedules() {

        const schedules =
            await this.orm.searchRead(
                "pm.activity.schedule",
                [
                    ["project_id", "=", this.projectId]
                ],
                [
                    "id",
                    "category",
                ]
            );

        const scheduleIds =
            schedules.map(s => s.id);

        const lines =
            scheduleIds.length
                ? await this.orm.searchRead(
                    "pm.activity.schedule.line",
                    [
                        ["schedule_id", "in", scheduleIds]
                    ],
                    [
                        "id",
                        "name",
                        "schedule_id",
                    ]
                )
                : [];

        schedules.forEach(schedule => {

            schedule.lines =
                lines.filter(
                    l =>
                        l.schedule_id[0]
                        === schedule.id
                );
        });

        this.state.activitySchedules =
            schedules;
    }

    async addScheduleTask(category) {

            let schedule =
                this.getSchedule(category);

            if (!schedule) {

                const ids =
                    await this.orm.create(
                        "pm.activity.schedule",
                        [{
                            project_id: this.projectId,
                            category: category,
                        }]
                    );

                schedule = {
                    id: ids[0],
                    category: category,
                    lines: [],
                };

                this.state.activitySchedules.push(
                    schedule
                );
            }

            const lineIds =
                await this.orm.create(
                    "pm.activity.schedule.line",
                    [{
                        schedule_id: schedule.id,
                        name: "New Task",
                    }]
                );

            schedule.lines.push({
                id: lineIds[0],
                name: "New Task",
            });
        }

        async updateScheduleTask(lineId, ev) {

        const value =
            ev.target.value;

        await this.orm.write(
            "pm.activity.schedule.line",
            [lineId],
            {
                name: value,
            }
        );

        this.state.activitySchedules.forEach(schedule => {

            const line =
                schedule.lines.find(
                    l => l.id === lineId
                );

            if (line) {
                line.name = value;
            }
        });
    }

    async deleteScheduleTask(lineId) {

        await this.orm.unlink(
            "pm.activity.schedule.line",
            [lineId]
        );

        this.state.activitySchedules.forEach(schedule => {

            schedule.lines =
                schedule.lines.filter(
                    line => line.id !== lineId
                );
        });
    }

    getScheduleTitle(category) {

            if (category === "last_week") {
                return "Last Week's Tasks";
            }

            if (category === "this_week") {
                return "This Week's Tasks";
            }

            return "Planning for Next Week";
        }

        getScheduleLines(category) {

        const schedule =
            this.getSchedule(category);

        return schedule
            ? schedule.lines
            : [];
    }

    // =========================================================
    // TIMELINE
    // =========================================================

    async reloadTimeline() {

        const timeline =
            await this.orm.call(
                "pm.project",
                "get_timeline_data",
                [this.projectId]
            );

        this.state.timeline =
            timeline || {};
    }

    openScurve() {
    this.state.selectedProjectId = this.projectId;
    this.state.showScurve = true;
    }

    closeScurve() {
        this.state.showScurve = false;
        this.state.selectedProjectId = null;
    }

    async uploadPhotos(ev) {
        const files = ev.target.files;

        for (const file of files) {
            const base64 = await this.fileToBase64(file);

            await this.orm.create(
                "pm.weekly.report.photo",
                [{
                    project_id: this.projectId,
                    name: file.name,
                    image: base64.split(",")[1],
                }]
            );
        }

        await this.reloadPhotos();
    }

    async updatePhotoCaption(photoId, ev) {
        await this.orm.write(
            "pm.weekly.report.photo",
            [photoId],
            {
                name: ev.target.value,
            }
        );
    }

    async deletePhoto(photoId) {
        await this.orm.unlink(
            "pm.weekly.report.photo",
            [photoId]
        );

        await this.reloadPhotos();
    }

    fileToBase64(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.readAsDataURL(file);
        });
    }

    async reloadPhotos() {
        const photos = await this.orm.searchRead(
            "pm.weekly.report.photo",
            [["project_id", "=", this.projectId]],
            ["id", "name", "image"]
        );

        this.state.photos = photos;
    }

    async exportPDF() {
        const action = await this.orm.call(
            "pm.project",
            "action_export_pdf",
            [this.projectId]
        );

        this.action.doAction(action);
    }

}


registry.category("actions").add(
    "pm_weekly_report.weekly_report_action",
    WeeklyReport
);