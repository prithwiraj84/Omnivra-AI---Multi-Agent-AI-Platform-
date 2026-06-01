import type { MediaServiceItem } from '@/types'
import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { MediaServiceCard } from '@/components/dashboard/media-service-card'
import { Stagger, StaggerItem } from '@/components/common/reveal'

export interface MediaServicesProps {
  services: MediaServiceItem[]
}

/**
 * MediaServices — "Media Services" card: a vertical list of MediaServiceCard rows
 * (Speech-to-Text / Text-to-Speech / Image Generation).
 */
export function MediaServices({ services }: MediaServicesProps) {
  return (
    <GlassCard className="space-y-4">
      <SectionHeader label="Media Services" />
      {services.length === 0 ? (
        <p className="py-8 text-center text-xs text-zinc-500">No media generated yet — image / TTS / STT usage appears here.</p>
      ) : (
        <Stagger className="space-y-2.5">
          {services.map((service) => (
            <StaggerItem key={service.name}>
              <MediaServiceCard service={service} />
            </StaggerItem>
          ))}
        </Stagger>
      )}
    </GlassCard>
  )
}
