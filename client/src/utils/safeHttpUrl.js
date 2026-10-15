// Only ever render http(s) URLs as hrefs, so a stored javascript:/data: URL can't execute on click.
export function safeHttpUrl(value) {
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:" ? value : null;
  } catch {
    return null;
  }
}
