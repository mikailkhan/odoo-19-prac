/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

export class UnisphereDashboard extends Component {
    static template = "unisphere_university.Dashboard";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            data: null,
            selectedTermId: null,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData(termId = null) {
        this.state.loading = true;
        try {
            const data = await this.orm.call("unisphere.dashboard", "get_dashboard_data", [], {
                term_id: termId || this.state.selectedTermId,
            });
            this.state.data = data;
            if (!this.state.selectedTermId && data.active_term_id) {
                this.state.selectedTermId = data.active_term_id;
            }
        } catch (error) {
            console.error("Failed to load UniSphere Dashboard data:", error);
            this.notification.add("Could not load dashboard data.", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    async onTermChange(ev) {
        const termId = parseInt(ev.target.value, 10);
        this.state.selectedTermId = termId || null;
        await this.loadData(this.state.selectedTermId);
    }

    // Quick Action Handlers
    openCreateStudent() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "unisphere.student",
            views: [[false, "form"]],
            target: "current",
        });
    }

    openCreateSection() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "unisphere.course.section",
            views: [[false, "form"]],
            target: "current",
        });
    }

    openTakeAttendance() {
        this.action.doAction({
            name: "Take Class Attendance",
            type: "ir.actions.act_window",
            res_model: "unisphere.attendance.wizard",
            views: [[false, "form"]],
            target: "new",
        });
    }

    openRecordGrades() {
        this.action.doAction({
            name: "Quick Grade Entry",
            type: "ir.actions.act_window",
            res_model: "unisphere.grade.wizard",
            views: [[false, "form"]],
            target: "new",
        });
    }

    openCreateFee() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "unisphere.fee",
            views: [[false, "form"]],
            target: "current",
        });
    }

    // Navigation drilldown handlers
    openStudentsList() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "unisphere.student",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openStudent(studentId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "unisphere.student",
            res_id: studentId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openFacultyList() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "unisphere.faculty",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openSectionsList() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "unisphere.course.section",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openFeesList(filter = null) {
        const context = {};
        if (filter === "overdue") {
            context.search_default_filter_overdue = 1;
        } else if (filter === "unpaid") {
            context.search_default_filter_unpaid = 1;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "unisphere.fee",
            views: [[false, "list"], [false, "pivot"], [false, "form"]],
            context: context,
            target: "current",
        });
    }

    openRecord(model, resId) {
        if (!model || !resId) return;
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("unisphere_dashboard", UnisphereDashboard);
