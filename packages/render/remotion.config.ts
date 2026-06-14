import { Config } from "@remotion/cli/config";

// 출력 이미지 포맷 (렌더 속도/품질 균형)
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// 세로 쇼츠 고해상도 인코딩 기본값
Config.setCodec("h264");
