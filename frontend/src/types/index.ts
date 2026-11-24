export interface TaskItem {
  id: string;
  title: string;
  description?: string;
  source: string;
  status: 'pending' | 'in_progress' | 'stalled' | 'overdue' | 'completed';
  deadline?: string;
  verification_evidence?: string;
  created_at: string;
}

export interface PendingActionItem {
  id: string;
  tool_name: string;
  parameters: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  summary: string;
  status: 'pending_approval' | 'approved' | 'rejected' | 'executed';
  created_at: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  actionRequired?: any;
  sourcesChecked?: string[];
  timestamp: string;
}
