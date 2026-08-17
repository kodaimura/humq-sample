const DEFAULT_MIN_LOADING_MS = 600;

export const wait = (ms: number) =>
  new Promise<void>((resolve) => window.setTimeout(resolve, ms));

export const waitAtLeast = async (
  startedAt: number,
  minMs = DEFAULT_MIN_LOADING_MS,
) => {
  const remainingMs = minMs - (Date.now() - startedAt);
  if (remainingMs > 0) {
    await wait(remainingMs);
  }
};

export const waitForProcessingPaint = () =>
  new Promise<void>((resolve) => {
    let resolved = false;

    const finish = () => {
      if (resolved) return;
      resolved = true;
      resolve();
    };

    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(finish);
    });
    window.setTimeout(finish, 50);
  });
