var WidgetsData = class AzClockWidgetsData {
    constructor(widgetsData) {
        if (WidgetsData._singleton) {
            console.warn('AppIcons Taskbar has been already initialized');
            return WidgetsData._singleton;
        }

        WidgetsData._singleton = widgetsData;
    }

    static getDefault() {
        return WidgetsData._singleton;
    }

    static set data(widgetsData) {
        WidgetsData._singleton = widgetsData;
    }

    static get data() {
        return WidgetsData.getDefault();
    }

    destroy() {
        WidgetsData._singleton = null;
    }
};
