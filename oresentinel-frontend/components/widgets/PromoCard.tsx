import Image from 'next/image';
import { Card } from '@/components/ui/Card';

/**
 * Bottom-right promotional card from the mockup ("Data-driven mining.
 * A stronger, greener India.") with the excavator photograph.
 *
 * Replace /public/mining-excavator.jpg with your own licensed asset —
 * the file currently shipped is a neutral placeholder background.
 */
export default function PromoCard() {
  return (
    <Card className="relative overflow-hidden">
      <div className="relative h-[150px] w-full">
        <Image
          src="/mining-excavator.svg"
          alt="Excavators working an open-pit manganese mine"
          fill
          sizes="(max-width: 1280px) 40vw, 320px"
          className="object-cover"
          priority={false}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-ink/90 via-ink/45 to-transparent" />
        <div className="absolute inset-x-0 bottom-0 p-4">
          <p className="text-[13px] font-bold leading-snug text-white">
            Data-driven mining.
            <br />
            A stronger, greener India.
          </p>
        </div>
      </div>
    </Card>
  );
}
