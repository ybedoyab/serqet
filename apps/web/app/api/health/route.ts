export function GET() {
  return Response.json({
    ok: true,
    service: "serqet",
    commit: process.env.NEXT_PUBLIC_COMMIT_SHA || "dev",
  });
}
