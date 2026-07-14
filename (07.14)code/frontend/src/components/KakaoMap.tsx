import { useEffect, useRef } from "react";
import "./KakaoMap.css";

declare global {
  interface Window {
    kakao: any;
  }
}

export interface MapPolygon {
  path: [number, number][]; // [lat, lng][]
  color: string;
  label?: string;
}

export interface MapPin {
  lat: number;
  lng: number;
  label: string;
  color: string;
}

interface KakaoMapProps {
  center: { lat: number; lng: number };
  polygons?: MapPolygon[];
  pins?: MapPin[];
  height?: number;
}

let sdkLoadPromise: Promise<void> | null = null;

function loadKakaoSdk(): Promise<void> {
  if (window.kakao?.maps) return Promise.resolve();
  if (sdkLoadPromise) return sdkLoadPromise;

  const appKey = import.meta.env.VITE_KAKAO_JS_KEY;
  sdkLoadPromise = new Promise((resolve, reject) => {
    if (!appKey) {
      reject(new Error("VITE_KAKAO_JS_KEY가 설정되지 않았습니다."));
      return;
    }
    const script = document.createElement("script");
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${appKey}&autoload=false&libraries=services`;
    script.onload = () => window.kakao.maps.load(() => resolve());
    script.onerror = () => reject(new Error("Kakao Maps SDK 로드 실패"));
    document.head.appendChild(script);
  });
  return sdkLoadPromise;
}

export function KakaoMap({ center, polygons = [], pins = [], height = 260 }: KakaoMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const errorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;

    loadKakaoSdk()
      .then(() => {
        if (cancelled || !containerRef.current) return;
        const { kakao } = window;
        const map = new kakao.maps.Map(containerRef.current, {
          center: new kakao.maps.LatLng(center.lat, center.lng),
          level: 4,
        });

        polygons.forEach((poly) => {
          const path = poly.path.map(([lat, lng]) => new kakao.maps.LatLng(lat, lng));
          new kakao.maps.Polygon({
            map,
            path,
            strokeWeight: 2,
            strokeColor: poly.color,
            strokeOpacity: 0.9,
            fillColor: poly.color,
            fillOpacity: 0.18,
          });
        });

        pins.forEach((pin) => {
          const position = new kakao.maps.LatLng(pin.lat, pin.lng);
          const marker = new kakao.maps.Marker({ map, position });
          const overlay = new kakao.maps.CustomOverlay({
            position,
            yAnchor: 2.4,
            content: `<div style="background:${pin.color};color:#fff;font-size:11px;font-weight:700;padding:3px 8px;border-radius:10px;white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,0.25)">${pin.label}</div>`,
          });
          overlay.setMap(map);
          void marker;
        });
      })
      .catch((err) => {
        if (errorRef.current) {
          errorRef.current.textContent = `지도를 불러올 수 없습니다: ${err.message}`;
        }
      });

    return () => {
      cancelled = true;
    };
  }, [center.lat, center.lng, polygons, pins]);

  return (
    <div className="kakaomap-wrap" style={{ height }}>
      <div ref={containerRef} className="kakaomap-container" />
      <div ref={errorRef} className="kakaomap-error" />
    </div>
  );
}
