import Link from "next/link"

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-8">
          貓咪餵食記錄系統
        </h1>
        <p className="text-center mb-8 text-lg">
          記錄和管理您的貓咪的餵食情況
        </p>
        <div className="flex justify-center gap-4">
          <Link
            href="/login"
            className="rounded-lg px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90"
          >
            登入系統
          </Link>
        </div>
      </div>
    </main>
  )
}
