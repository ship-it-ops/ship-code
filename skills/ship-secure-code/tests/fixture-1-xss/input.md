# Synthetic Input for Fixture 1: Stored XSS via dangerouslySetInnerHTML

You are reviewing the following two files. Apply the `ship-secure-code` rubric.

## File: `app/components/MessageView.tsx`

```tsx
'use client';

import { useEffect, useState } from 'react';

interface Message {
  id: string;
  authorName: string;
  bodyHtml: string;     // rich-text body stored in the DB
  postedAt: string;
}

export function MessageView({ messageId }: { messageId: string }) {
  const [message, setMessage] = useState<Message | null>(null);

  useEffect(() => {
    fetch(`/api/messages/${messageId}`)
      .then((r) => r.json())
      .then(setMessage);
  }, [messageId]);

  if (!message) return null;

  return (
    <article>
      <h3>{message.authorName}</h3>
      <time>{message.postedAt}</time>
      <div dangerouslySetInnerHTML={{ __html: message.bodyHtml }} />
    </article>
  );
}
```

## File: `app/api/messages/[id]/route.ts`

```ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { getServerSession } from 'next-auth';

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const session = await getServerSession();
  if (!session) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const result = await db.query(
    'SELECT id, author_name, body_html, posted_at FROM messages WHERE id = $1',
    [params.id],
  );

  return NextResponse.json(result.rows[0]);
}
```

---

Apply the ship-secure-code rubric and produce a structured review.
