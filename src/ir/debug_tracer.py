import json
import time
import inspect
from collections import defaultdict

class DebugTracer:
    """
    A tracer to record debugging information, primarily for generator execution.
    This file was reconstructed based on its usage in the project, especially
    the @trace_method decorator in `src/generators/instrumentation.py` and
    sample trace files.
    """
    def __init__(self, enabled=False, capture_stack=False):
        self.enabled = enabled
        self.capture_stack = capture_stack
        self.traces = []
        self.call_stats = defaultdict(int)
        self.start_time = time.time()
        self.call_depth = 0
        self.call_id_counter = 0
        self.call_stack = []  # Stack to store call IDs

    def _get_current_call_id(self):
        return self.call_stack[-1] if self.call_stack else 0

    def _record_event(self, method_name, event_type, data):
        """A central method to create and store a trace record."""
        trace_record = {
            'method_name': method_name,
            'event_type': event_type,
            'data': data,
            'timestamp': time.time(),
            'call_depth': self.call_depth,
        }

        stack = []
        if self.capture_stack:
            # Skip the current frame and the one before it (the caller in this class)
            for frame_info in inspect.stack()[2:]:
                stack.append({
                    'file': frame_info.filename,
                    'line': frame_info.lineno,
                    'function': frame_info.function,
                })
        trace_record['stack_trace'] = stack
        self.traces.append(trace_record)

    def trace_call(self, method_name, params):
        """Traces a method call event."""
        if not self.enabled:
            return

        self.call_stats[method_name] += 1
        self.call_id_counter += 1
        call_id = self.call_id_counter

        parent_call_id = self._get_current_call_id()
        
        data = params.copy()
        data['_call_id'] = call_id
        data['_parent_call_id'] = parent_call_id
        data['_call_count'] = self.call_stats[method_name]

        self.call_stack.append(call_id)
        self._record_event(method_name, 'call', data)
        self.call_depth += 1

    def trace_return(self, method_name, return_info):
        """Traces a method return event."""
        if not self.enabled:
            return

        self.call_depth -= 1
        call_id = self.call_stack.pop() if self.call_stack else 0
        
        data = return_info.copy()
        data['_call_id'] = call_id
        self._record_event(method_name, 'return', data)

    def trace_exception(self, method_name, exception):
        """Traces an exception event."""
        if not self.enabled:
            return

        self.call_depth -= 1
        call_id = self.call_stack.pop() if self.call_stack else 0

        data = {
            '_call_id': call_id,
            'exception_type': type(exception).__name__,
            'exception_str': str(exception),
        }
        self._record_event(method_name, 'exception', data)

    def trace_info(self, method_name, info):
        """Records a generic informational event within a method."""
        if not self.enabled:
            return

        data = info.copy()
        data['_call_id'] = self._get_current_call_id()
        self._record_event(method_name, 'info', data)

    def get_traces(self):
        """Returns all collected traces."""
        return self.traces

    def get_call_stats(self):
        """Returns statistics on how many times each method was called."""
        return dict(self.call_stats)

    def to_json(self, trace_path):
        """Serializes all trace data to a JSON file."""
        if not self.enabled:
            return

        duration = time.time() - self.start_time
        output = {
            'trace': self.traces,
            'call_stats': self.get_call_stats(),
            'duration': duration,
            'total_entries': len(self.traces),
        }

        try:
            with open(trace_path, 'w') as f:
                json.dump(output, f, indent=2)
        except IOError as e:
            print(f"Error writing trace file: {e}")
