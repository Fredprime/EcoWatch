import { WorkspacePage } from './WorkspacePage';

export function SimpleWorkspace({ title, description }: { title: string; description: string }) {
  return <WorkspacePage title={title} description={description} />;
}
