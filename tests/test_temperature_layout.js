const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const context = {};
vm.createContext(context);
const panel = require('./helpers/command_panels').load(context);
const sensors = [
    ...Array.from({length: 16}, (_, i) => ({group: 'coretemp', name: 'Core ' + i, value: 60})),
    {group: 'amdgpu', name: 'edge', value: 81},
    {group: 'nvme', name: 'Composite', value: 40},
    ...['TM0P','TTLD','TTRD','TW0P','Ts0P','Th1H','TA0V','UNKNOWN'].map(name => ({group: 'applesmc', name, value: 50})),
];
const columns = panel._temperatureColumns(sensors);
assert.equal(columns.length, 4);
const critical = new Set(['CPU', 'GPU', 'Memória RAM', 'Armazenamento']);
columns.forEach((column, index) => column.forEach(group => assert.equal(critical.has(group.title), index < 2)));
const displayed = columns.flat().flatMap(group => group.items);
assert.equal(displayed.length, sensors.length);
assert.equal(new Set(displayed).size, sensors.length);
assert.equal(panel._temperatureColumns([]).length, 4);
assert.equal(panel._temperatureCategory({group:'applesmc',name:'UNKNOWN'}), 'Outros sensores');
console.log('OK: four columns, critical/auxiliary separation, no lost or duplicated sensors.');
