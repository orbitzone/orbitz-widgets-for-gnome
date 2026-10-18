/* Pure reminder scheduling: shared by the clock cards and regression tests. */
var stamp = task => [task.date, task.time, task.reminder].join('|');
var countdown = milliseconds => {
    if (milliseconds <= 0) return 'Começando agora';
    const seconds = Math.ceil(milliseconds / 1000);
    if (seconds >= 3600) return `Começa em ${Math.floor(seconds / 3600)}h ${Math.floor(seconds % 3600 / 60)}min`;
    if (seconds >= 60) return `Começa em ${Math.floor(seconds / 60)}min ${String(seconds % 60).padStart(2, '0')}s`;
    return `Começa em ${seconds}s`;
};
var collect = function(data, external, now = Date.now()) {
    const items = [], seen = new Set();
    const due = (start, lead) => Number.isFinite(start) && Number.isFinite(lead) && lead >= 0 && lead <= 10080 && now >= start - lead * 60000 && now < start + 60000;
    for (const task of data.tasks || []) {
        if (task.done || !task.time || task.dismissed === stamp(task)) continue;
        const start = new Date(`${task.date}T${task.time}:00`).getTime(), lead = Number(task.reminder ?? 10);
        if (!due(start, lead)) continue;
        items.push({key: `task|${task.id}|${stamp(task)}`, type: 'task', id: task.id, stamp: stamp(task), title: task.text,
            source: 'Tarefa', start, lead, day: task.date, time: task.time});
    }
    for (const account of external.accounts || []) for (const calendar of account.calendars || []) {
        const prefix = `${account.id}|${calendar.id}|`;
        for (const [cacheKey, cache] of Object.entries(external.cache || {})) {
            if (!cacheKey.startsWith(prefix)) continue;
            for (const event of cache.events || []) {
                if (event.all_day) continue;
                const start = Date.parse(event.start);
                const leads = (event.alarm_minutes || []).filter(n => Number.isFinite(n) && n >= 0 && n <= 10080);
                const lead = leads.length ? Math.max(...leads) : 10;
                const identity = `${event.key}|${start}|${lead}`;
                if (seen.has(identity)) continue;
                seen.add(identity);
                // A converted task uses its own reminder and completion/dismissal state.
                if ((data.tasks || []).some(t => t.external_source?.key === event.key && t.date === event.start.slice(0, 10) && t.time === event.start.slice(11, 16))) continue;
                if (!due(start, lead)) continue;
                items.push({key: `event|${identity}`, type: 'event', title: event.title, start, lead,
                    source: account.provider === 'ics' ? calendar.name : `${account.label} · ${calendar.name}`,
                    day: event.start.slice(0, 10), time: event.start.slice(11, 16)});
            }
        }
    }
    return items.sort((a, b) => a.start - b.start || a.key.localeCompare(b.key));
};
