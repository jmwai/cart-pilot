import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-20">
      <div className="mx-auto px-4 sm:px-6 lg:px-8 py-12" style={{ maxWidth: 'calc(100% - var(--chatbox-width) - 2rem)' }}>
        <div className="grid grid-cols-2 md:grid-cols-2 gap-8">

          <div>
            <h3 className="font-bold text-gray-900 mb-4">Cart Pilot</h3>
            <p className="text-gray-600 text-sm">This is not a real store. It is a demo for cloud run hackathon. Built with 
              <Link href="https://google.github.io/adk-docs/" className="text-blue-500 hover:text-blue-600">Agent Development Kit</Link>
            </p>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-200 text-center text-sm text-gray-600">
          ©2025 Cart Pilot. All Rights Reserved.
        </div>
      </div>
    </footer>
  );
}
