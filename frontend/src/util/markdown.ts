import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";
import remarkRehype from "remark-rehype";
import rehypeSanitize from "rehype-sanitize";
import rehypeStringify from "rehype-stringify";

/**
 * Converts markdown content to HTML using remark + rehype
 * Supports GitHub Flavored Markdown (GFM) including lists, links, bold, italic, etc.
 */
export function parseMarkdownToHTML(content: string): string {
  if (!content) return "";

  const file = unified()
    .use(remarkParse) // Parse markdown to AST
    .use(remarkGfm) // Support GitHub Flavored Markdown (tables, strikethrough, task lists, etc.)
    .use(remarkRehype) // Convert markdown AST to HTML AST
    .use(rehypeSanitize) // Sanitize HTML to prevent XSS attacks
    .use(rehypeStringify) // Convert HTML AST to string
    .processSync(content);

  let html = String(file);

  // Apply Tailwind CSS classes to the generated HTML elements
  html = html.replace(
    /<h1>/g,
    '<h1 class="text-2xl font-bold mb-4 text-slate-900">',
  );
  html = html.replace(
    /<h2>/g,
    '<h2 class="text-xl font-semibold mb-3 text-slate-800">',
  );
  html = html.replace(
    /<h3>/g,
    '<h3 class="text-lg font-semibold mb-2 text-slate-800">',
  );
  html = html.replace(
    /<h4>/g,
    '<h4 class="text-base font-semibold mb-2 text-slate-800">',
  );
  html = html.replace(
    /<h5>/g,
    '<h5 class="text-sm font-semibold mb-2 text-slate-800">',
  );
  html = html.replace(
    /<h6>/g,
    '<h6 class="text-xs font-semibold mb-2 text-slate-800">',
  );

  html = html.replace(/<p>/g, '<p class="mb-3 leading-relaxed">');

  html = html.replace(
    /<strong>/g,
    '<strong class="font-semibold text-slate-900">',
  );
  html = html.replace(/<em>/g, '<em class="italic">');

  html = html.replace(
    /<a href="/g,
    '<a target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline" href="',
  );

  html = html.replace(/<ul>/g, '<ul class="list-disc ml-6 mb-4 space-y-1">');
  html = html.replace(/<ol>/g, '<ol class="list-decimal ml-6 mb-4 space-y-1">');
  html = html.replace(/<li>/g, '<li class="mb-1 leading-relaxed">');

  html = html.replace(
    /<blockquote>/g,
    '<blockquote class="border-l-4 border-gray-300 pl-4 italic my-4">',
  );
  html = html.replace(
    /<code>/g,
    '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">',
  );
  html = html.replace(
    /<pre>/g,
    '<pre class="bg-gray-100 p-4 rounded-lg overflow-x-auto my-4">',
  );

  return html;
}
