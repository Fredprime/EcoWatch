import { Link } from 'react-router-dom';
import { Notice } from './Notice';

export function SignInPrompt({ what }: { what: string }) {
  return (
    <Notice variant="info" role="note" title="Sign in required.">
      {what} <Link to="/login">Sign in</Link> to continue. Access is enforced by the server.
    </Notice>
  );
}
