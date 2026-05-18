/** @odoo-module **/

import { registry } from "@web/core/registry";
import { WBSMain } from "./wbs_main";

registry.category("actions").add("pm_wbs_main", WBSMain);