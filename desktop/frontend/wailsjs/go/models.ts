export namespace main {
	
	export class PDFItem {
	    class: string;
	    course: string;
	    content: string;
	    filename: string;
	    path: string;
	    size: number;
	    mtime: string;
	
	    static createFrom(source: any = {}) {
	        return new PDFItem(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.class = source["class"];
	        this.course = source["course"];
	        this.content = source["content"];
	        this.filename = source["filename"];
	        this.path = source["path"];
	        this.size = source["size"];
	        this.mtime = source["mtime"];
	    }
	}
	export class ScanResult {
	    root: string;
	    items: PDFItem[];
	
	    static createFrom(source: any = {}) {
	        return new ScanResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.root = source["root"];
	        this.items = this.convertValues(source["items"], PDFItem);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}

}

