/* One-level grouping. IDs survive reorder; invalid/cyclic relationships stay on desktop. */
var planGroups = function(data) {
    const ids = new Map(), duplicates = new Set();
    data.forEach((widget,index) => {
        const id = widget[0].Widget_Id;
        if (!id) return;
        if (ids.has(id)) duplicates.add(id);
        ids.set(id,index);
    });
    const groups = new Map();
    data.forEach((widget,index) => {
        const meta = widget[0];
        if (meta.Widget_Id && !duplicates.has(meta.Widget_Id) && meta.Box_IsGroup === 'true' && !meta.Parent_Id) groups.set(index,[]);
    });
    data.forEach((widget,index) => {
        const meta = widget[0], parent = ids.get(meta.Parent_Id);
        if (!meta.Parent_Id || parent === undefined || parent === index || duplicates.has(meta.Parent_Id) ||
            meta.Box_IsGroup === 'true' || data[parent][0].Box_IsGroup !== 'true' || data[parent][0].Parent_Id) return;
        if (!groups.has(parent)) groups.set(parent,[]);
        groups.get(parent).push(index);
    });
    return groups;
};

var settingsOrder = function(data) {
    const groups = planGroups(data);
    const children = new Set([...groups.values()].flat());
    const order = [];
    data.forEach((_widget,index) => {
        if (children.has(index)) return;
        order.push(index);
        order.push(...(groups.get(index) || []));
    });
    return order;
};
