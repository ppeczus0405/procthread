import platform
import multiprocessing as mp
from multiprocessing.pool import ThreadPool
from timeit import default_timer as timer
from os import cpu_count
from sys import version
from enum import Enum, auto

class TagState(Enum):
    OPEN = auto()
    CLOSED = auto()
    OPENCLOSED = auto()
    
class HtmlTag:
    def __init__(self, tag_name, arguments, open_closed, content, newline):      
        # Conditional nl - newline add
        nl = lambda n: "\n" if n == True else ""
        # Conditional ads - add space
        ads = lambda s: " " if s == True else ""
        # Add closing tag
        closed = lambda : "</" + tag_name + ">"
        # Add open tag
        open = lambda :  "<" + tag_name + ads(arguments != "") + arguments + "> " + content + " "
        
        if open_closed == TagState.OPEN:
            self.tag_content = open() + nl(newline)
        elif open_closed == TagState.CLOSED:
            self.tag_content = closed() + nl(newline)
        else:
            self.tag_content = open() + closed() + nl(newline)
    
    def get(self):
        return self.tag_content 
            
class Table:
    def __init__(self, columns_names):
        self.columns_names = columns_names
        self.rows = []

    def add_row(self, row):
        self.rows.append(row)

    def rows_count(self):
        return len(self.rows)

    def columns(self):
        return len(self.columns_names)
    
    def to_html(self):
        html_content = HtmlTag("table", "", TagState.OPEN, "", True).get()
        
        def columns_names():
            s = HtmlTag("tr", "", TagState.OPEN, "", True).get()
            
            # Column names add
            for cn in self.columns_names:
                s += HtmlTag("th", "", TagState.OPENCLOSED, cn, True).get()
            
            s += HtmlTag("tr", "", TagState.CLOSED, "", True).get()
            return s
        
        def add_row(row):
            s = HtmlTag("tr", "", TagState.OPEN, "", True).get()
            
            for value in row:
                if type(value) is float:
                    s += HtmlTag("td", "", TagState.OPENCLOSED, str(round(value, 3)), True).get()
                else:
                    s += HtmlTag("td", "", TagState.OPENCLOSED, str(value), True).get()
            
            s += HtmlTag("tr", "", TagState.CLOSED, "", True).get()
            return s

        def all_rows():
            s = str()
            for r in self.rows:
                s += add_row(r)
            return s
        
        html_content += columns_names()
        html_content += all_rows()
        html_content += HtmlTag("table", "", TagState.CLOSED, "", True).get()

        return html_content

class Document:
    def __init__(self, html_content):
        self.html_content = html_content
    
    def save(self, filename):
        with open(filename, 'w') as file:
            file.write(self.html_content)

class DocumentBuilder:
    STYLE = """<style>
table {
    font-family: arial, sans-serif;
    border-collapse: collapse;
}

td, th {
    border: 1px solid #dddddd;
    text-align: center;
    padding: 8px;
}

tr:nth-child(even) {
    background-color: #ededed;
}
</style>\n\n"""
    
    def __init__(self):
        self.content  = HtmlTag("!DOCTYPE", "html", TagState.OPEN, "", True).get()
        self.content += HtmlTag("html", "", TagState.OPEN, "", True).get()
        self.content += HtmlTag("head", "", TagState.OPEN, "", True).get()
        self.content += DocumentBuilder.STYLE
        self.content += HtmlTag("head", "", TagState.CLOSED, "", True).get()
        self.content += HtmlTag("body", "", TagState.OPEN, "", True).get()
    
    def add_header(self):
        inside = "Multithreading/Multiprocessing benchmark results"
        self.content += HtmlTag("h1", "", TagState.OPENCLOSED, inside, True).get()
        return self
    
    def add_environment(self):
        # Content table
        CT = {"Python version: ": platform.python_version(), 
              "Interpreter: ": platform.python_implementation(),
              "Interpreter version: ": version, 
              "Operating system: ": platform.system(), 
              "Operating system version: " : platform.release(),
              "Processor: ": (lambda s: s if s != "" else "Can't determine")(platform.processor()),
              "CPUs: ": str(cpu_count())
             }
        
        header_content = "Execution environment"
        self.content += HtmlTag("h2", "", TagState.OPENCLOSED, header_content, True).get()
        
        for key, value in CT.items():
            tag_content = key + value + "<br/>"
            self.content += HtmlTag("span", "", TagState.OPENCLOSED, tag_content, True).get()
            
        return self
    
    def add_results(self, result_table):
        header_content = "Test results"
        desc = "The following table shows detailed test results:"
        self.content += HtmlTag("h2", "", TagState.OPENCLOSED, header_content, True).get()
        self.content += HtmlTag("p", "", TagState.OPENCLOSED, desc, True).get()
        self.content += result_table.to_html()
        return self

    def add_summary(self, summary_table):
        header_content = "Summary"
        desc = "The following table shows the median of all results:"
        self.content += HtmlTag("h2", "", TagState.OPENCLOSED, header_content, True).get()
        self.content += HtmlTag("p", "", TagState.OPENCLOSED, desc, True).get()
        self.content += summary_table.to_html()
        return self
    
    def build(self):
        author = "App author: Patryk Pęczak"
        self.content += HtmlTag("p", "", TagState.OPENCLOSED, author, True).get()
        self.content += HtmlTag("body", "", TagState.CLOSED, "", True).get()
        self.content += HtmlTag("html", "", TagState.CLOSED, "", True).get()
        return Document(self.content)

class Computation:
    ARGUMENTS = [15972490, 80247910, 92031257, 75940266, 97986012, 87599664, 75231321, 11138524,
                 68870499, 11872796, 79132533, 40649382, 63886074, 53146293, 36914087, 62770938]
     
    COMPUTATION_TAGS = ["Execution: ", "1 thread (s)", "4 threads (s)", "4 processes (s)",
                        "processes based on number of CPU's(s)"]
    THRD_ARGS = [1, 4]
    PROC_ARGS = [4, mp.cpu_count()]
    
    def __init__(self, iterations):
        self.iterations = iterations

    def get_tables(self):
        def compute(process : bool):
            times = []
            ptargs = Computation.PROC_ARGS if process == True else Computation.THRD_ARGS
            compute_f = Computation._solve_processes if process == True else Computation._solve_threads
            
            for pt in ptargs:
                start = timer()
                compute_f(pt)
                times.append(timer() - start)
            
            return times 
        
        def median(args):
            n = len(args)
            if n == 0:
                return 0
            args.sort()
            mid = int(n / 2)
            return args[mid] if n % 2 == 1 else (args[mid - 1] + args[mid]) / 2 
        
        result_table = Table(Computation.COMPUTATION_TAGS)
        summary_table = Table(Computation.COMPUTATION_TAGS)
        
        grouped = [[], [], [], []]
        
        for iteration in range(self.iterations):
            presult = compute(True)
            tresult = compute(False)
            record = [iteration + 1] + tresult + presult
            result_table.add_row(record)
            targslen = len(Computation.THRD_ARGS)
            pargslen = len(Computation.PROC_ARGS)
            for i in range(0, targslen):
                grouped[i].append(tresult[i])
            for i in range(0, pargslen):
                grouped[targslen + i].append(presult[i])
        
        medians = ["Median:"] + [median(margs) for margs in grouped]
        summary_table.add_row(medians)
        
        return result_table, summary_table

    @staticmethod
    def _solve_processes(processes_num):
        with mp.Pool(processes_num) as pool:
            return pool.map(Computation._mp_f, Computation.ARGUMENTS)
    
    @staticmethod
    def _solve_threads(threads_num):
        with ThreadPool(threads_num) as pool:
            return pool.map(Computation._mp_f, Computation.ARGUMENTS)
    
    @staticmethod
    def _mp_f(n):
        result = 0
        for i in range(1, n + 1):
            result += (n - i) * i
        return result

RECORDS_NUMBER = 5

if __name__ == "__main__":
    comps = Computation(RECORDS_NUMBER)
    result, summary = comps.get_tables()
    
    doc = DocumentBuilder().add_header().add_environment().add_results(result).add_summary(summary).build()
    doc.save("index.html")