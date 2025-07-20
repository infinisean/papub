"""
Sessions comparator for firewall health metrics
"""
import re
from typing import Dict, Any, Set, List
from .base import BaseComparator, ComparisonResult, ComparisonStatus
from .utils import extract_numbers, clean_whitespace

class SessionsComparator(BaseComparator):
    """Comparator for 'show session all' command output"""
    
    def __init__(self):
        super().__init__("show_session_all")
    
    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse session output into structured data"""
        sessions = []
        session_states = {}
        protocols = {}
        
        lines = output.strip().split('\n')
        total_sessions = 0
        
        for line in lines:
            line = clean_whitespace(line)
            if not line:
                continue
                
            # Look for session count information
            if 'total sessions' in line.lower() or 'session count' in line.lower():
                numbers = extract_numbers(line)
                if numbers:
                    total_sessions = max(numbers)  # Take the largest number found
                continue
            
            # Parse individual session lines
            # Typical format: ID src-zone dst-zone proto src-ip dst-ip state
            if re.match(r'^\d+\s+', line):  # Line starts with session ID
                parts = line.split()
                if len(parts) >= 6:
                    session = {
                        'id': parts[0],
                        'src_zone': parts[1] if len(parts) > 1 else 'unknown',
                        'dst_zone': parts[2] if len(parts) > 2 else 'unknown', 
                        'protocol': parts[3] if len(parts) > 3 else 'unknown',
                        'src_ip': parts[4] if len(parts) > 4 else 'unknown',
                        'dst_ip': parts[5] if len(parts) > 5 else 'unknown',
                        'state': parts[6] if len(parts) > 6 else 'active'
                    }
                    
                    sessions.append(session)
                    
                    # Count states and protocols
                    state = session['state']
                    protocol = session['protocol']
                    
                    session_states[state] = session_states.get(state, 0) + 1
                    protocols[protocol] = protocols.get(protocol, 0) + 1
        
        # If we didn't find total sessions from summary, use session count
        if total_sessions == 0:
            total_sessions = len(sessions)
        
        return {
            'sessions': sessions,
            'total_sessions': total_sessions,
            'session_states': session_states,
            'protocols': protocols,
            'active_sessions': session_states.get('active', 0),
            'closed_sessions': session_states.get('closed', 0)
        }
    
    def compare(self, pre_data: Dict[str, Any], post_data: Dict[str, Any]) -> ComparisonResult:
        """Compare session data"""
        pre_total = pre_data.get('total_sessions', 0)
        post_total = post_data.get('total_sessions', 0)
        
        pre_states = pre_data.get('session_states', {})
        post_states = post_data.get('session_states', {})
        
        pre_protocols = pre_data.get('protocols', {})
        post_protocols = post_data.get('protocols', {})
        
        # Calculate changes
        total_change = post_total - pre_total
        percentage_change = self._calculate_percentage_change(pre_total, post_total)
        
        # Compare session states
        state_changes = {}
        all_states = set(pre_states.keys()) | set(post_states.keys())
        for state in all_states:
            pre_count = pre_states.get(state, 0)
            post_count = post_states.get(state, 0)
            if pre_count != post_count:
                state_changes[state] = {
                    'pre': pre_count,
                    'post': post_count,
                    'change': post_count - pre_count
                }
        
        # Determine status and message
        if abs(percentage_change) <= 5:  # Within 5% is considered normal
            status = ComparisonStatus.SUCCESS
            message = f"Session count stable ✅ ({post_total} sessions, {total_change:+d})"
        elif percentage_change < -20:  # More than 20% drop is concerning
            status = ComparisonStatus.ERROR
            message = f"Significant session drop ❌ ({post_total} sessions, {percentage_change:.1f}% decrease)"
        elif percentage_change > 50:  # More than 50% increase might indicate issues
            status = ComparisonStatus.WARNING
            message = f"Large session increase ⚠️ ({post_total} sessions, {percentage_change:.1f}% increase)"
        elif abs(percentage_change) > 10:  # 10-20% change warrants attention
            status = ComparisonStatus.WARNING
            change_type = "increase" if percentage_change > 0 else "decrease"
            message = f"Moderate session {change_type} ⚠️ ({post_total} sessions, {percentage_change:.1f}%)"
        else:
            status = ComparisonStatus.SUCCESS
            message = f"Session count normal ✅ ({post_total} sessions, {percentage_change:.1f}%)"
        
        # Prepare detailed metrics
        metrics = {
            'pre_total': pre_total,
            'post_total': post_total,
            'total_change': total_change,
            'percentage_change': percentage_change,
            'pre_active': pre_states.get('active', 0),
            'post_active': post_states.get('active', 0)
        }
        
        details = {
            'state_changes': state_changes,
            'protocol_changes': self._compare_protocols(pre_protocols, post_protocols),
            'pre_states': pre_states,
            'post_states': post_states
        }
        
        return ComparisonResult(
            status=status,
            message=message,
            details=details,
            metrics=metrics
        )
    
    def _compare_protocols(self, pre_protocols: Dict[str, int], post_protocols: Dict[str, int]) -> Dict[str, Dict[str, int]]:
        """Compare protocol distributions"""
        protocol_changes = {}
        all_protocols = set(pre_protocols.keys()) | set(post_protocols.keys())
        
        for protocol in all_protocols:
            pre_count = pre_protocols.get(protocol, 0)
            post_count = post_protocols.get(protocol, 0)
            if pre_count != post_count:
                protocol_changes[protocol] = {
                    'pre': pre_count,
                    'post': post_count,
                    'change': post_count - pre_count
                }
        
        return protocol_changes


class SessionCountComparator(BaseComparator):
    """Comparator for 'show session all filter count yes' command output"""
    
    def __init__(self):
        super().__init__("show_session_all_filter_count_yes")
    
    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse session count output"""
        lines = output.strip().split('\n')
        total_sessions = 0
        
        for line in lines:
            # Look for total session count
            numbers = extract_numbers(line)
            if numbers and ('total' in line.lower() or 'session' in line.lower()):
                total_sessions = max(numbers)
                break
        
        return {
            'total_sessions': total_sessions,
            'raw_output': output
        }
    
    def compare(self, pre_data: Dict[str, Any], post_data: Dict[str, Any]) -> ComparisonResult:
        """Compare session counts"""
        pre_count = pre_data.get('total_sessions', 0)
        post_count = post_data.get('total_sessions', 0)
        
        change = post_count - pre_count
        percentage_change = self._calculate_percentage_change(pre_count, post_count)
        
        # Determine status
        if abs(percentage_change) <= 5:
            status = ComparisonStatus.SUCCESS
            message = f"Session count stable ✅ ({post_count} sessions)"
        elif percentage_change < -15:
            status = ComparisonStatus.ERROR
            message = f"Session count dropped ❌ ({post_count} sessions, {change:+d})"
        elif abs(percentage_change) > 10:
            status = ComparisonStatus.WARNING
            message = f"Session count changed ⚠️ ({post_count} sessions, {change:+d})"
        else:
            status = ComparisonStatus.SUCCESS
            message = f"Session count normal ✅ ({post_count} sessions, {change:+d})"
        
        return ComparisonResult(
            status=status,
            message=message,
            metrics={
                'pre_count': pre_count,
                'post_count': post_count,
                'change': change,
                'percentage_change': percentage_change
            }
        )