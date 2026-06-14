import { loadFont as loadKR } from "@remotion/google-fonts/NotoSansKR";
import { loadFont as loadArchivo } from "@remotion/google-fonts/Archivo";

// @remotion/google-fonts는 내부적으로 delayRender/continueRender를 처리하므로
// 렌더 시 폰트 로드 완료 후 프레임이 캡처됨 (CDN @import의 깜빡임 문제 해결).
const { fontFamily: KR } = loadKR("normal", {
  weights: ["400", "600", "700", "800", "900"],
  subsets: ["korean", "latin"],
});

const { fontFamily: NUM } = loadArchivo("normal", {
  weights: ["800", "900"],
  subsets: ["latin"],
});

export const FONT_KR = `${KR}, 'Apple SD Gothic Neo', system-ui, sans-serif`;
export const FONT_NUM = `${NUM}, ${KR}, system-ui, sans-serif`;
