#!/usr/bin/env python3
import json
import sys

def print_trace_stack(trace_file, target_call_id):
    """Print the call stack for a given _call_id"""
    with open(trace_file, 'r') as f:
        data = json.load(f)

    traces = data['traces']

    # Build a map of call_id -> trace entries
    call_map = {}
    for trace in traces:
        if 'data' in trace and '_call_id' in trace['data']:
            call_id = trace['data']['_call_id']
            if call_id not in call_map:
                call_map[call_id] = []
            call_map[call_id].append(trace)

    # Find the target trace
    if target_call_id not in call_map:
        print(f"Call ID {target_call_id} not found!")
        return

    # Build the call chain
    call_chain = []
    current_id = target_call_id

    while current_id is not None:
        if current_id not in call_map:
            break

        # Find the 'call' event for this ID
        call_event = None
        for trace in call_map[current_id]:
            if trace.get('event_type') == 'call':
                call_event = trace
                break

        if call_event:
            call_chain.append(call_event)
            current_id = call_event['data'].get('_parent_call_id')
        else:
            break

    # Print in reverse order (root to leaf)
    call_chain.reverse()

    print(f"Call Stack for _call_id: {target_call_id}")
    print("=" * 100)

    for i, trace in enumerate(call_chain):
        indent = "  " * i
        method = trace.get('method_name', 'unknown')
        call_id = trace['data'].get('_call_id', '?')
        parent_id = trace['data'].get('_parent_call_id', 'None')
        namespace = trace['data'].get('namespace', 'N/A')

        print(f"{indent}[{i}] call_id={call_id} parent={parent_id}")
        print(f"{indent}    method: {method}")
        print(f"{indent}    namespace: {namespace}")

        # Print relevant data
        data = trace['data']
        for key, value in data.items():
            if not key.startswith('_') and key != 'namespace':
                if len(str(value)) < 100:
                    print(f"{indent}    {key}: {value}")
        print()

    # Print detailed info for the target call
    print("=" * 100)
    print(f"Detailed info for _call_id {target_call_id}:")
    print("=" * 100)

    for trace in call_map[target_call_id]:
        print(f"\nEvent: {trace.get('event_type')}")
        print(f"Method: {trace.get('method_name')}")
        if 'data' in trace:
            for key, value in trace['data'].items():
                print(f"  {key}: {value}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <trace_file.json> <call_id>")
        sys.exit(1)

    trace_file = sys.argv[1]
    call_id = int(sys.argv[2])

    print_trace_stack(trace_file, call_id)
