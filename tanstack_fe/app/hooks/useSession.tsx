import { useEffect, useState } from 'react';
import { getSessionId } from '../utils/session';

export function useSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    const id = getSessionId();
    setSessionId(id);
  }, []);

  return sessionId;
}