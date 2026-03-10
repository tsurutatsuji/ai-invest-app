"use client"

import { useState } from "react"

export default function DashboardPage() {
  const [claudeKey, setClaudeKey] = useState("")
  const [telegramToken, setTelegramToken] = useState("")
  const [deployed, setDeployed] = useState(false)

  function handleDeploy(e: React.FormEvent) {
    e.preventDefault()
    if (!claudeKey || !telegramToken) return
    setDeployed(true)
  }

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-2xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold">セットアップ</h1>
          <p className="mt-2 text-gray-500">
            必要な情報を入力してデプロイを開始しましょう
          </p>
        </div>

        {/* Input Form */}
        <form
          onSubmit={handleDeploy}
          className="bg-white rounded-2xl shadow-md p-8 space-y-6"
        >
          <div>
            <label
              htmlFor="claude-key"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Claude APIキー
            </label>
            <input
              id="claude-key"
              type="password"
              value={claudeKey}
              onChange={(e) => setClaudeKey(e.target.value)}
              placeholder="sk-ant-api03-..."
              className="w-full border border-gray-300 rounded-xl py-3 px-4 font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
              required
            />
            <p className="mt-1 text-xs text-gray-400">
              Anthropic のダッシュボードから取得できます
            </p>
          </div>

          <div>
            <label
              htmlFor="telegram-token"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Telegram Bot トークン
            </label>
            <input
              id="telegram-token"
              type="password"
              value={telegramToken}
              onChange={(e) => setTelegramToken(e.target.value)}
              placeholder="123456789:ABCdef..."
              className="w-full border border-gray-300 rounded-xl py-3 px-4 font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
              required
            />
            <p className="mt-1 text-xs text-gray-400">
              Telegram の @BotFather から取得できます
            </p>
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white text-lg font-bold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200"
          >
            デプロイ開始
          </button>
        </form>

        {/* Deploy Result */}
        {deployed && (
          <div className="space-y-6">
            {/* Confirmation */}
            <div className="bg-green-50 border border-green-200 rounded-2xl p-6">
              <h2 className="text-lg font-bold text-green-800 mb-3">
                入力内容の確認
              </h2>
              <dl className="space-y-2 text-sm">
                <div className="flex gap-2">
                  <dt className="font-medium text-green-700 shrink-0">
                    Claude APIキー:
                  </dt>
                  <dd className="font-mono text-green-900 break-all">
                    {claudeKey.slice(0, 12)}...{claudeKey.slice(-4)}
                  </dd>
                </div>
                <div className="flex gap-2">
                  <dt className="font-medium text-green-700 shrink-0">
                    Telegram トークン:
                  </dt>
                  <dd className="font-mono text-green-900 break-all">
                    {telegramToken.slice(0, 10)}...{telegramToken.slice(-4)}
                  </dd>
                </div>
              </dl>
            </div>

            {/* Guide */}
            <div className="bg-white rounded-2xl shadow-md p-8 space-y-6">
              <h2 className="text-xl font-bold">次の手順ガイド</h2>

              <div className="space-y-4">
                <Step
                  number={1}
                  title="リポジトリをクローン"
                  command="git clone https://github.com/your-org/openclaw-bot.git && cd openclaw-bot"
                />
                <Step
                  number={2}
                  title="環境変数を設定"
                  command={`echo "ANTHROPIC_API_KEY=${claudeKey}" > .env\necho "TELEGRAM_BOT_TOKEN=${telegramToken}" >> .env`}
                />
                <Step
                  number={3}
                  title="依存パッケージをインストール"
                  command="npm install"
                />
                <Step
                  number={4}
                  title="ローカルで動作確認"
                  command="npm run dev"
                />
                <Step
                  number={5}
                  title="Vercel にデプロイ"
                  command="npx vercel --prod"
                />
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-sm text-yellow-800">
                <p className="font-bold mb-1">ヒント</p>
                <p>
                  Vercel CLI が未インストールの場合は、先に{" "}
                  <code className="bg-yellow-100 px-1 rounded">
                    npm i -g vercel
                  </code>{" "}
                  を実行してください。
                </p>
              </div>
            </div>
          </div>
        )}

        <p className="text-center">
          <a href="/" className="text-sm text-blue-600 hover:underline">
            ← トップへ戻る
          </a>
        </p>
      </div>
    </div>
  )
}

function Step({
  number,
  title,
  command,
}: {
  number: number
  title: string
  command: string
}) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(command)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="border border-gray-200 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="bg-blue-600 text-white text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center">
          {number}
        </span>
        <h3 className="font-medium">{title}</h3>
      </div>
      <div className="relative">
        <pre className="bg-gray-900 text-green-400 rounded-lg p-3 text-sm overflow-x-auto whitespace-pre-wrap">
          {command}
        </pre>
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 text-xs bg-gray-700 hover:bg-gray-600 text-white py-1 px-2 rounded transition"
        >
          {copied ? "コピー済み" : "コピー"}
        </button>
      </div>
    </div>
  )
}
