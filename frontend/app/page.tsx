import { ChatWindow } from "@/components/ChatWindow";

export default function HomePage() {
  return (
    <main className="flex h-screen flex-col">
      <header className="border-b border-gray-200 p-4">
        <h1 className="text-xl font-semibold">AkademiaTA Assistant</h1>
      </header>
      <div className="flex-1 overflow-hidden">
        <ChatWindow />
      </div>
    </main>
  );
}
