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

    if (errorRef.current) errorRef.current.textContent = "";

    loadKakaoSdk()
      .then(() => {
        if (cancelled || !containerRef.current) return;
        const { kakao } = window;
        const map = new kakao.maps.Map(containerRef.current, {
          center: new kakao.maps.LatLng(center.lat, center.lng),
          level: 4,
        });

        const bounds = new kakao.maps.LatLngBounds();

        polygons.forEach((poly) => {
          const path = poly.path.map(([lat, lng]) => new kakao.maps.LatLng(lat, lng));
          path.forEach((p: any) => bounds.extend(p));
          new kakao.maps.Polygon({
            map,
            path,
            strokeWeight: 2,
            strokeColor: poly.color,
            strokeOpacity: 0.9,
            fillColor: poly.color,
            fillOpacity: 0.18,
          });

          if (poly.label && poly.path.length > 0) {
            const centerLat = poly.path.reduce((s, [lat]) => s + lat, 0) / poly.path.length;
            const centerLng = poly.path.reduce((s, [, lng]) => s + lng, 0) / poly.path.length;
            const labelOverlay = new kakao.maps.CustomOverlay({
              position: new kakao.maps.LatLng(centerLat, centerLng),
              content: `<div style="background:${poly.color};color:#fff;font-size:12px;font-weight:800;padding:5px 12px;border-radius:999px;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,0.3);border:2px solid #fff">${poly.label}</div>`,
            });
            labelOverlay.setMap(map);
          }
        });

        // 가게 이름은 항상 띄우지 않고, 작은 색상 점만 표시 + 마우스 오버 시 이름 툴팁(title)
        pins.forEach((pin) => {
          const position = new kakao.maps.LatLng(pin.lat, pin.lng);
          bounds.extend(position);
          const dot = new kakao.maps.CustomOverlay({
            position,
            content: `<div title="${pin.label}" style="width:10px;height:10px;border-radius:50%;background:${pin.color};border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.4)"></div>`,
          });
          dot.setMap(map);
        });

        if (!bounds.isEmpty()) {
          map.setBounds(bounds, 40, 40, 40, 40);
        }
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
