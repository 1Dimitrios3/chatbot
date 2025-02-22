import { createFileRoute } from '@tanstack/react-router'
import { Link } from '@tanstack/react-router'
import { Button } from "../components/ui/button";

export const Route = createFileRoute('/')({
  component: Home,
})

function Home() {
  return (
    <div className="flex flex-col items-center justify-center h-screen space-y-6">
    <h3 className="text-center text-2xl font-semibold">
      Hello! <br /> Ask me anything you want to know about Grow Suite.
    </h3>
    <Link to="/chat">
        <Button variant="default" size="lg">Go to Chat</Button>
      </Link>
  </div>
  )
}
