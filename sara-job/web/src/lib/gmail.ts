// Real, working "jump into Gmail" links — no backend needed for this part.
// Opens Gmail's own compose UI (not a generic mailto:) pre-filled with the
// drafted text, in a new tab, so review-and-send stays a human action in
// Gmail itself. Once the backend calls email-agent's create_draft() for
// real, this can instead deep-link straight to the created draft.

export function gmailComposeUrl({
  to,
  subject,
  body,
}: {
  to?: string;
  subject?: string;
  body: string;
}): string {
  const params = new URLSearchParams({ view: "cm", fs: "1", body });
  if (to) params.set("to", to);
  if (subject) params.set("su", subject);
  return `https://mail.google.com/mail/?${params.toString()}`;
}
