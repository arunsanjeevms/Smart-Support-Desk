/**
 * The text that is compared, built the same way as the backend
 * (``ticket_text`` in apps/similarity/engines.py): the title, then the description,
 * with runs of whitespace collapsed.
 */
export function similarText(title: string | null | undefined, description: string | null | undefined): string {
  const clean = (value: string | null | undefined) => (value ?? '').replace(/\s+/g, ' ').trim();
  const head = clean(title);
  const body = clean(description);
  if (head && body) {
    return /[.!?]$/.test(head) ? `${head} ${body}` : `${head}. ${body}`;
  }
  return head || body;
}

/** 0.684 -> 68 */
export function similarityPercent(score: number): number {
  return Math.round(Math.min(Math.max(score, 0), 1) * 100);
}
