
// teams_ui.js - Handles Teams Selection Modals

// Store current selection state
let selectedClassId = null;
let selectedAssignmentIds = [];

// Expose functions to allow backend to trigger UI
eel.expose(showClassesSelection);
function showClassesSelection(classes) {
    console.log("Showing classes selection:", classes);
    const list = document.getElementById("teams-class-list");
    list.innerHTML = "";

    // Create Radio Buttons (Single Select)
    classes.forEach(cls => {
        const item = document.createElement("div");
        item.style.cssText = "display: flex; align-items: center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 8px; border: 1px solid transparent; cursor: pointer; transition: all 0.2s;";

        item.innerHTML = `
            <input type="radio" name="teams_class" value="${cls.id}" id="cls_${cls.id}" style="margin-right: 15px; transform: scale(1.2);">
            <label for="cls_${cls.id}" style="cursor: pointer; width: 100%;">
                <div style="color: #fff; font-weight: bold;">${cls.displayName}</div>
                <div style="color: #aaa; font-size: 0.8rem;">${cls.description || ""} ${cls.section ? "(" + cls.section + ")" : ""}</div>
            </label>
        `;

        // Click anywhere on item selects radio
        item.onclick = () => {
            document.getElementById(`cls_${cls.id}`).checked = true;
            handleClassSelect(cls.id);

            // Visual highlight
            Array.from(list.children).forEach(c => c.style.borderColor = "transparent");
            item.style.borderColor = "#00ffff";
        };

        list.appendChild(item);
    });

    document.getElementById("teams-class-modal").style.display = "flex";
}

function handleClassSelect(id) {
    selectedClassId = id;
    const btn = document.getElementById("teams-class-confirm-btn");
    btn.disabled = false;
    btn.style.cursor = "pointer";
    btn.style.opacity = "1";

    // Attach confirm handler dynamically
    btn.onclick = () => {
        if (!selectedClassId) return;
        document.getElementById("teams-class-modal").style.display = "none";
        // Send back to python
        eel.handle_class_selected(selectedClassId);
    };
}

eel.expose(showAssignmentsSelection);
function showAssignmentsSelection(assignments) {
    console.log("Showing assignments selection:", assignments);
    const list = document.getElementById("teams-assignment-list");
    list.innerHTML = "";
    selectedAssignmentIds = [];

    // Create Checkboxes (Multi Select)
    assignments.forEach(asn => {
        const item = document.createElement("div");
        item.style.cssText = "display: flex; align-items: center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 8px; border: 1px solid transparent; cursor: pointer; transition: all 0.2s;";

        // Format Due Date
        const due = new Date(asn.dueDateTime).toLocaleDateString() + " " + new Date(asn.dueDateTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        item.innerHTML = `
            <input type="checkbox" value="${asn.id}" id="asn_${asn.id}" style="margin-right: 15px; transform: scale(1.2);">
            <label for="asn_${asn.id}" style="cursor: pointer; width: 100%;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #fff; font-weight: bold;">${asn.displayName}</span>
                    <span style="color: #00ffff; font-size: 0.9rem;">${asn.maxPoints} pts</span>
                </div>
                <div style="color: #aaa; font-size: 0.8rem;">Due: ${due}</div>
            </label>
        `;

        // Click handler
        const checkbox = item.querySelector("input");
        item.onclick = (e) => {
            if (e.target !== checkbox && e.target.tagName !== "LABEL") {
                checkbox.checked = !checkbox.checked;
            }
            updateAssignmentSelection(checkbox.value, checkbox.checked);

            item.style.borderColor = checkbox.checked ? "#00ffff" : "transparent";
        };

        // Handle direct checkbox click
        checkbox.onclick = (e) => {
            e.stopPropagation();
            updateAssignmentSelection(checkbox.value, checkbox.checked);
            item.style.borderColor = checkbox.checked ? "#00ffff" : "transparent";
        };

        list.appendChild(item);
    });

    document.getElementById("teams-assignment-modal").style.display = "flex";
    updateConfirmBtnState();
}

function updateAssignmentSelection(id, isChecked) {
    if (isChecked) {
        if (!selectedAssignmentIds.includes(id)) selectedAssignmentIds.push(id);
    } else {
        selectedAssignmentIds = selectedAssignmentIds.filter(x => x !== id);
    }
    updateConfirmBtnState();
}

function updateConfirmBtnState() {
    const btn = document.getElementById("teams-assignment-confirm-btn");
    const hasSelection = selectedAssignmentIds.length > 0;

    btn.disabled = !hasSelection;
    btn.style.cursor = hasSelection ? "pointer" : "not-allowed";
    btn.style.opacity = hasSelection ? "1" : "0.5";

    btn.onclick = () => {
        if (!selectedAssignmentIds.length) return;
        document.getElementById("teams-assignment-modal").style.display = "none";
        // Send back to python
        eel.handle_assignments_selected(selectedAssignmentIds);
    };
}

function closeTeamsModal(id) {
    document.getElementById(id).style.display = "none";
    // Notify cancellation if needed
    eel.handle_selection_cancelled();
}
