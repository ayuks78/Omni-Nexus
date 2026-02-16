import subprocess
import tempfile
import os
import time
import re


class CodeExecutor:
    def __init__(self):
        self.supported = ["python", "javascript", "html", "css"]
        self.timeout = 30
        self.execution_history = []

    def execute(self, code, language, stdin=""):
        language = language.lower().strip()
        if language not in self.supported:
            return {"success": False, "output": "", "error": f"Linguagem '{language}' nao suportada.", "execution_time": 0, "language": language}

        start = time.time()
        try:
            if language == "python":
                result = self._exec_python(code, stdin)
            elif language == "javascript":
                result = self._exec_js(code, stdin)
            elif language in ("html", "css"):
                result = self._validate_web(code, language)
            else:
                result = {"success": False, "output": "", "error": "Nao implementado"}
        except Exception as e:
            result = {"success": False, "output": "", "error": str(e)}

        result["execution_time"] = round((time.time() - start) * 1000, 2)
        result["language"] = language
        self.execution_history.append({"language": language, "success": result["success"], "time": result["execution_time"], "timestamp": time.time()})
        if len(self.execution_history) > 50:
            self.execution_history = self.execution_history[-25:]
        return result

    def _exec_python(self, code, stdin=""):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            path = f.name
        try:
            p = subprocess.run(['python3', path], capture_output=True, text=True, timeout=self.timeout, input=stdin or None)
            return {"success": p.returncode == 0, "output": p.stdout, "error": p.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": "Timeout excedido"}
        except FileNotFoundError:
            return {"success": False, "output": "", "error": "Python3 nao encontrado"}
        finally:
            try:
                os.unlink(path)
            except:
                pass

    def _exec_js(self, code, stdin=""):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(code)
            path = f.name
        try:
            p = subprocess.run(['node', path], capture_output=True, text=True, timeout=self.timeout, input=stdin or None)
            return {"success": p.returncode == 0, "output": p.stdout, "error": p.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": "Timeout excedido"}
        except FileNotFoundError:
            return {"success": False, "output": "", "error": "Node.js nao encontrado"}
        finally:
            try:
                os.unlink(path)
            except:
                pass

    def _validate_web(self, code, language):
        errors = []
        if language == "html":
            open_tags = re.findall(r'<(\w+)[^>]*>', code)
            close_tags = re.findall(r'</(\w+)>', code)
            void_el = {'br', 'hr', 'img', 'input', 'meta', 'link'}
            open_tags = [t.lower() for t in open_tags if t.lower() not in void_el]
            if len(open_tags) != len(close_tags):
                errors.append(f"Tags desbalanceadas: {len(open_tags)} abertas, {len(close_tags)} fechadas")
        elif language == "css":
            if code.count('{') != code.count('}'):
                errors.append("Chaves desbalanceadas")
        if errors:
            return {"success": False, "output": code[:1000], "error": "\n".join(errors)}
        return {"success": True, "output": f"[{language.upper()}] Estrutura valida!\n\n{code[:2000]}", "error": ""}

    def get_history(self):
        return self.execution_history
