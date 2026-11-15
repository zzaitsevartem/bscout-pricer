import { PageTransition } from '@/shared/ui/PageTransition';
import { Suspense } from 'react';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { DeviceClient } from './DeviceClient';
export default async function DevicePage({ params }: { params: Promise<{ model_key: string }> }) {
  const { model_key: modelKey } = await params;
  return (
    <>
      <Header />
      <PageTransition>
        <Suspense
          fallback={
            <p role="status" className="p-8 text-body-subtle">
              Загрузка устройства…
            </p>
          }
        >
          <DeviceClient key={modelKey} modelKey={modelKey} />
        </Suspense>
      </PageTransition>
      <Footer />
    </>
  );
}
