// app/routes/__root.tsx
import type { ReactNode } from 'react'
import {
  Outlet,
  createRootRoute,
  HeadContent,
  Scripts,
  Link
} from '@tanstack/react-router'
import appCss from "../styles/app.css?url"
import { DefaultCatchBoundary } from '~/components/ui/DefaultCatchBoundary'
import { NotFound } from '~/components/ui/NotFound'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient();

export const Route = createRootRoute({
  head: () => ({
    meta: [
      {
        charSet: 'utf-8',
      },
      {
        name: 'viewport',
        content: 'width=device-width, initial-scale=1',
      },
      {
        title: 'AI Assistant',
      },
    ]
  }),
  errorComponent: (props) => {
    return (
      <RootDocument>
        <DefaultCatchBoundary {...props} />
      </RootDocument>
    )
  },
  notFoundComponent: () => <NotFound />,
  component: RootComponent,
})

function RootComponent() {
  return (
    <QueryClientProvider client={queryClient}>
    <RootDocument>
      <Outlet />
    </RootDocument>
  </QueryClientProvider>
  )
}

function RootDocument({ children }: Readonly<{ children: ReactNode }>) {
  const searchParams = Route.useSearch();
  return (
    <html>
      <head>
        <HeadContent />
        <link rel="stylesheet" href={appCss} />
      </head>
      <body>
      <div className="p-2 flex gap-2 text-lg bg-zinc-900">
          <Link
            to="/"
            activeProps={{
              className: 'font-bold',
            }}
            activeOptions={{ exact: true }}
          >
            Home
          </Link>{' '}
          <div className="relative group">
            <span className="cursor-pointer text-white">Upload</span>
            <div className="absolute left-0 hidden group-hover:block bg-zinc-800 p-2 rounded shadow-lg">
              <Link
                to="/pdf/upload"
                className="block px-2 py-1 hover:bg-zinc-700"
                activeProps={{ className: 'font-medium' }}
                search={searchParams}
              >
                PDF
              </Link>
              <Link
                to="/csv/upload"
                className="block px-2 py-1 hover:bg-zinc-700"
                activeProps={{ className: 'font-medium' }}
                search={searchParams}
              >
                CSV
              </Link>
            </div>
          </div>
          <Link
            to="/train"
            activeProps={{
              className: 'font-bold',
            }}
            search={searchParams}
          >
            Train
          </Link>{' '}
          <Link
            to="/chat"
            activeProps={{
              className: 'font-bold',
            }}
          >
            Chat
          </Link>{' '}
        </div>
        <hr />
        {children}
        <Scripts />
      </body>
    </html>
  )
}