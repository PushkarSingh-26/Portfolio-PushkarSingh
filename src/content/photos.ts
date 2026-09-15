import type { StaticImageData } from "next/image";
import datathon from "@/photos/datathon.jpg";
import techzoom from "@/photos/techzoom.jpg";
import infinitrix from "@/photos/infinitrix.jpg";
import portrait from "@/photos/portrait.jpg";

export interface Photo {
  src: StaticImageData;
  /** Describes what is actually in the frame — no claims beyond that. */
  alt: string;
}

/** Keyed by the achievement's event name in content/recognition.ts. */
export const achievementPhotos: Record<string, Photo> = {
  "National Level Machine Learning Datathon": {
    src: datathon,
    alt: "Pushkar Singh holding three certificates from the datathon, outside the SRM Institute of Science and Technology campus.",
  },
  TECHZOOM: {
    src: techzoom,
    alt: "Pushkar Singh receiving the TECHZOOM certificate on stage at SRM Institute of Science and Technology, alongside faculty members and another participant.",
  },
  "INFINITRIX project presentation": {
    src: infinitrix,
    alt: "Pushkar Singh holding the INFINITRIX trophy and certificate in the grounds of Loyola College, Chennai.",
  },
};

export const portraitPhoto: Photo = {
  src: portrait,
  alt: "Pushkar Singh.",
};
