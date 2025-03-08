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
      Hello there...
    </h3>
    <h4> 
      Upload and analyze a <i>PDF</i> or <i>CSV</i> file and start a chat.
    </h4>
    <Link to="/pdf/upload">
        <Button variant="default" size="lg">Upload a file</Button>
      </Link>
  </div>
  )
}
