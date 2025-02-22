// app/routes/__root.tsx
import type { ReactNode } from 'react'
import {
  Outlet,
  createRootRoute,
  HeadContent,
  Scripts,
  Link,
} from '@tanstack/react-router'
import appCss from "../styles/app.css?url"
import { DefaultCatchBoundary } from '~/components/ui/DefaultCatchBoundary'
import { NotFound } from '~/components/ui/NotFound'

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
    <RootDocument>
      <Outlet />
    </RootDocument>
  )
}

function RootDocument({ children }: Readonly<{ children: ReactNode }>) {
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
          <Link
            to="/upload"
            activeProps={{
              className: 'font-bold',
            }}
          >
            Upload
          </Link>{' '}
          <Link
            to="/train"
            activeProps={{
              className: 'font-bold',
            }}
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