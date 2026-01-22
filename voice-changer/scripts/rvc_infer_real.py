#!/usr/bin/env python3
"""
RVC 推理完整实现 - 使用真正的 RVC Pipeline 进行声音转换
"""
import os
import sys
import argparse
import numpy as np
import torch
import librosa
import soundfile as sf
from pathlib import Path
import subprocess
import traceback

# 添加 RVC 路径
SCRIPT_DIR = Path(__file__).parent.parent
RVC_CODE_PATH = SCRIPT_DIR / 'models' / 'Retrieval-based-Voice-Conversion-WebUI'
sys.path.insert(0, str(RVC_CODE_PATH))

def get_device():
    """获取运行设备"""
    # 优先使用 CPU 以避免 MPS 内存问题
    return "cpu"

class RVCConfig:
    """RVC 配置类"""
    def __init__(self, device="cpu"):
        self.device = torch.device(device)
        self.is_half = False
        self.x_pad = 3
        self.x_query = 3
        self.x_center = 1
        self.x_max = 32

def load_rvc_model(model_path, device="cpu"):
    """
    加载 RVC 模型

    Returns:
        (net_g, tgt_sr, if_f0, version)
    """
    print(f"正在加载 RVC 模型: {os.path.basename(model_path)}")

    # 加载 checkpoint
    cpt = torch.load(model_path, map_location=device, weights_only=False)

    # 如果没有 config，从文件名推断
    if "config" not in cpt:
        print("  检测到预训练模型，从文件名推断配置...")
        import re

        filename = os.path.basename(model_path)
        # 匹配格式: f0D40k.pth, G48k.pth 等
        match = re.match(r'^(f0)?(D|G)(\d+)k\.pth', filename)

        if match:
            has_f0 = match.group(1) == 'f0'
            sr = int(match.group(3)) * 1000
            print(f"  解析: F0={has_f0}, 采样率={sr}Hz")

            # 构建配置
            if sr == 40000:
                config = [1024, 32, 192, 192, 768, 2, 6, 3, 0.1, '1',
                         [3,7,11], [[1,3,5], [1,3,5], [1,3,5]],
                         [10,10,2,2], 512, [3,3,3,3], 256, 256, 40000]
            elif sr == 48000:
                config = [1024, 32, 192, 192, 768, 2, 6, 3, 0.1, '1',
                         [3,7,11], [[1,3,5], [1,3,5], [1,3,5]],
                         [10,10,2,2], 512, [3,3,3,3], 256, 256, 48000]
            else:  # 32000
                config = [1024, 32, 192, 192, 768, 2, 6, 3, 0.1, '1',
                         [3,7,11], [[1,3,5], [1,3,5], [1,3,5]],
                         [10,10,2,2], 512, [3,3,3,3], 256, 256, 32000]

            # 转换权重格式
            if 'model' in cpt and 'weight' not in cpt:
                cpt['weight'] = cpt['model']

            cpt['config'] = config
            cpt['f0'] = 1 if has_f0 else 0
            cpt['version'] = 'v2'
        else:
            # 使用默认配置
            print("  使用默认配置 (40kHz v2)")
            cpt['config'] = [1024, 32, 192, 192, 768, 2, 6, 3, 0.1, '1',
                           [3,7,11], [[1,3,5], [1,3,5], [1,3,5]],
                           [10,10,2,2], 512, [3,3,3,3], 256, 256, 40000]
            cpt['f0'] = 1
            cpt['version'] = 'v2'
            if 'model' in cpt and 'weight' not in cpt:
                cpt['weight'] = cpt['model']

    # 检查 speaker embedding
    if "emb_g.weight" in cpt.get("weight", {}):
        cpt["config"][-3] = cpt["weight"]["emb_g.weight"].shape[0]
    else:
        cpt["config"][-3] = 1
        print("  预训练模型，使用 n_spk=1")

    tgt_sr = cpt["config"][-1]
    if_f0 = cpt.get("f0", 1)
    version = cpt.get("version", "v1")

    print(f"  模型版本: {version}")
    print(f"  目标采样率: {tgt_sr} Hz")
    print(f"  使用 F0: {if_f0}")

    # 导入模型类
    from infer.lib.infer_pack.models import (
        SynthesizerTrnMs256NSFsid,
        SynthesizerTrnMs256NSFsid_nono,
        SynthesizerTrnMs768NSFsid,
        SynthesizerTrnMs768NSFsid_nono,
    )

    synthesizer_class = {
        ("v1", 1): SynthesizerTrnMs256NSFsid,
        ("v1", 0): SynthesizerTrnMs256NSFsid_nono,
        ("v2", 1): SynthesizerTrnMs768NSFsid,
        ("v2", 0): SynthesizerTrnMs768NSFsid_nono,
    }

    net_g = synthesizer_class.get(
        (version, if_f0), SynthesizerTrnMs256NSFsid
    )(*cpt["config"], is_half=False)

    del net_g.enc_q
    net_g.load_state_dict(cpt["weight"], strict=False)
    net_g.eval().to(device)

    return net_g, tgt_sr, if_f0, version

def voice_conversion(input_audio, output_audio, model_path, voice_config=None, f0up_key=0,
                     f0_method="harvest", device="cpu"):
    """
    执行 RVC 语音转换 - 使用完整的 RVC Pipeline
    """
    if voice_config is None:
        voice_config = {}

    # 从 voice_config 中提取参数
    f0up_key = voice_config.get('f0up_key', f0up_key)
    f0_method = voice_config.get('f0_method', f0_method)

    print("=" * 50)
    print("RVC 真实语音转换")
    print("=" * 50)

    # 加载模型
    try:
        net_g, tgt_sr, if_f0, version = load_rvc_model(model_path, device)
    except Exception as e:
        print(f"模型加载失败: {e}")
        traceback.print_exc()
        return False

    # 加载 HuBERT 模型（使用 RVC 的 get_hubert_model 函数）
    print("正在加载 HuBERT 模型...")
    try:
        # 使用 RVC 的 get_hubert_model 函数
        from infer.lib.jit.get_hubert import get_hubert_model

        # 查找 HuBERT 模型文件
        hubert_model_path = SCRIPT_DIR / 'models' / 'rvc_models' / 'weizuo' / 'rvc-model' / 'assets' / 'hubert' / 'hubert_base.pt'
        if not hubert_model_path.exists():
            # 尝试其他位置
            hubert_model_path = SCRIPT_DIR / 'models' / 'rvc_models' / 'hubert' / 'hubert_base.pt'

        if not hubert_model_path.exists():
            raise FileNotFoundError(f"HuBERT 模型文件不存在: {hubert_model_path}")

        print(f"  加载文件: {hubert_model_path}")
        hubert_model = get_hubert_model(str(hubert_model_path), torch.device(device))
        hubert_model.eval()
        print(f"  HuBERT 模型加载成功")
    except Exception as e:
        print(f"  HuBERT 加载失败: {e}")
        traceback.print_exc()
        return False

    # 创建配置
    config = RVCConfig(device)

    # 导入 Pipeline
    try:
        from infer.modules.vc.pipeline import Pipeline
        from infer.lib.audio import load_audio
    except Exception as e:
        print(f"  无法导入 Pipeline: {e}")
        traceback.print_exc()
        return False

    # 创建 Pipeline
    pipeline = Pipeline(tgt_sr, config)

    # 加载音频
    print("正在加载音频...")
    try:
        audio = load_audio(input_audio, 16000)
        audio_max = np.abs(audio).max() / 0.95
        if audio_max > 1:
            audio = audio / audio_max
    except Exception as e:
        print(f"  音频加载失败: {e}")
        traceback.print_exc()
        return False

    # RVC 推理参数
    sid = 0  # speaker ID
    file_index = voice_config.get('index_path', '')
    # 展开 ~ 路径
    if file_index:
        file_index = os.path.expanduser(file_index)
    index_rate = voice_config.get('index_rate', 0.75)
    filter_radius = voice_config.get('filter_radius', 3)
    resample_sr = voice_config.get('resample_sr', 0)
    rms_mix_rate = voice_config.get('rms_mix_rate', 0.25)
    protect = voice_config.get('protect', 0.33)

    print(f"正在执行 RVC 推理...")
    print(f"  音高调整: {f0up_key:+d} 半音")
    print(f"  F0 方法: {f0_method}")
    if file_index and os.path.exists(file_index):
        print(f"  使用 Index 文件: {os.path.basename(file_index)}")
    else:
        file_index = ""

    # 执行 RVC Pipeline
    try:
        times = [0, 0, 0]  # 计时

        audio_opt = pipeline.pipeline(
            hubert_model,
            net_g,
            sid,
            audio,
            input_audio,
            times,
            f0up_key,
            f0_method,
            file_index,
            index_rate,
            if_f0,
            filter_radius,
            tgt_sr,
            resample_sr if resample_sr >= 16000 else tgt_sr,
            rms_mix_rate,
            version,
            protect,
        )

        # 保存输出
        print("正在保存输出...")
        sf.write(output_audio, audio_opt, tgt_sr)

        print(f"✅ RVC 转换完成！")
        print(f"输出文件: {output_audio}")
        print(f"处理时间: 提取特征={times[0]:.2f}s, F0提取={times[1]:.2f}s, 推理={times[2]:.2f}s")
        return True

    except Exception as e:
        print(f"RVC 推理失败: {e}")
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='RVC 真实语音转换')
    parser.add_argument('input', help='输入音频文件')
    parser.add_argument('-o', '--output', required=True, help='输出音频文件')
    parser.add_argument('-m', '--model', required=True, help='RVC 模型路径 (.pth)')
    parser.add_argument('-p', '--pitch', type=int, default=0, help='音高调整（半音）')
    parser.add_argument('-f', '--f0-method', default='harvest',
                       choices=['harvest', 'pm', 'crepe'], help='F0 提取方法')
    parser.add_argument('-d', '--device', help='运行设备（cpu/cuda/mps）')
    parser.add_argument('-i', '--index', help='Index 文件路径（提高音质）')
    parser.add_argument('--index-rate', type=float, default=0.75, help='Index 混合率')
    parser.add_argument('--filter-radius', type=int, default=3, help='F0 过滤半径')
    parser.add_argument('--resample-sr', type=int, default=0, help='重采样率')
    parser.add_argument('--rms-mix-rate', type=float, default=0.25, help='RMS 混合率')
    parser.add_argument('--protect', type=float, default=0.33, help='保护清音比例')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"输入文件不存在: {args.input}")
        sys.exit(1)

    if not os.path.exists(args.model):
        print(f"模型文件不存在: {args.model}")
        sys.exit(1)

    device = args.device or get_device()
    print(f"使用设备: {device.upper()}")

    # 构建语音配置
    voice_config = {
        'f0up_key': args.pitch,
        'f0_method': args.f0_method,
        'index_path': args.index,
        'index_rate': args.index_rate,
        'filter_radius': args.filter_radius,
        'resample_sr': args.resample_sr,
        'rms_mix_rate': args.rms_mix_rate,
        'protect': args.protect,
    }

    success = voice_conversion(
        args.input,
        args.output,
        args.model,
        voice_config=voice_config,
        device=device
    )

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
