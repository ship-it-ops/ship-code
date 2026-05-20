# Synthetic Input for Fixture 3: Missing AuthZ (IDOR)

You are reviewing the following Next.js App Router route. Apply the `ship-secure-code` rubric.

## File: `app/api/documents/[id]/route.ts`

```ts
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { prisma } from '@/lib/prisma';

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  const document = await prisma.document.findUnique({
    where: { id: params.id },
    include: { author: { select: { id: true, displayName: true } } },
  });

  if (!document) {
    return NextResponse.json({ error: 'not found' }, { status: 404 });
  }

  return NextResponse.json(document);
}

export async function DELETE(req: NextRequest, { params }: { params: { id: string } }) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  await prisma.document.delete({ where: { id: params.id } });

  return NextResponse.json({ ok: true });
}
```

## Reference: `prisma/schema.prisma` (excerpt)

```prisma
model Document {
  id          String   @id @default(cuid())
  title       String
  bodyMd      String   @db.Text
  authorId    String
  author      User     @relation(fields: [authorId], references: [id])
  tenantId    String
  createdAt   DateTime @default(now())
}
```

---

Apply the ship-secure-code rubric and produce a structured review.
