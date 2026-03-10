import Link from "next/link"

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className="max-w-2xl text-center space-y-8">
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
          日本人向け OpenClaw
          <br />
          <span className="text-blue-600">簡単スタート</span>
        </h1>

        <p className="text-lg sm:text-xl text-gray-600 leading-relaxed">
          Claude AI と Telegram Bot を組み合わせた
          <br className="hidden sm:block" />
          自動化ツールを、誰でもかんたんにセットアップできます。
        </p>

        <p className="text-2xl font-semibold text-blue-600">
          技術ゼロでも1分で始められます
        </p>

        <Link
          href="/login"
          className="inline-block bg-blue-600 hover:bg-blue-700 text-white text-xl font-bold py-4 px-12 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200"
        >
          今すぐ始める
        </Link>

        <p className="text-sm text-gray-400">
          無料で始められます・クレジットカード不要
        </p>
      </div>
    </div>
  )
}
