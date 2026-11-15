"""Build an isolated editor helper that actually animates limbs during cloth tests."""
import os,json,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-secondary-v1';C=Path(__file__).resolve().parent
old=R/'private/jirai-proportion-v1/variant/ue/ProjectPBZ/Plugins/PBZModTools';src=C/'editor-tools/PBZModTools'
src.mkdir(parents=True,exist_ok=True)
if not (src/'Source').exists():
 shutil.copytree(old/'Source',src/'Source');shutil.copy2(old/'PBZModTools.uplugin',src/'PBZModTools.uplugin')
cpp=src/'Source/PBZModTools/Private/PBZModToolsLibrary.cpp';header=src/'Source/PBZModTools/Public/PBZModToolsLibrary.h'
s=cpp.read_text();h=header.read_text()
if 'UPBZModToolsLibrary::TestClothAnimation' not in s:
 f=s[s.index('FString UPBZModToolsLibrary::TestClothMotion('):]
 assert f.rstrip().endswith('}')
 f=f.replace('TestClothMotion(USkeletalMesh* Mesh, int32 Steps, float DeltaTime, float TravelCm)','TestClothAnimation(USkeletalMesh* Mesh, UAnimSequence* Animation, int32 Steps, float DeltaTime)')
 f=f.replace('if (!Mesh || Steps<1','const float TravelCm = -8.f;\n    if (!Animation || !Mesh || Steps<1',1)
 f=f.replace('C->SetSkeletalMesh(Mesh); C->SetUpdateClothInEditor(true);','C->SetSkeletalMesh(Mesh); C->SetUpdateClothInEditor(true);\n    C->SetAnimationMode(EAnimationMode::AnimationSingleNode); C->SetAnimation(Animation); C->SetPosition(0.f, false);')
 f=f.replace('C->UpdateComponentToWorld(); C->RefreshBoneTransforms();','C->SetPosition(FMath::Min(float(T), Animation->GetPlayLength()), false); C->TickAnimation(0.f, false);\n        C->UpdateComponentToWorld(); C->RefreshBoneTransforms();')
 f=f.replace('F->SetArrayField(TEXT("assets"),A); Frames.Add', '''F->SetArrayField(TEXT("assets"),A);
            TArray<TSharedPtr<FJsonValue>> Bones;
            for (const FTransform& B : C->GetComponentSpaceTransforms())
            {
                const FVector P = B.GetTranslation(); const FQuat Q = B.GetRotation();
                TArray<TSharedPtr<FJsonValue>> V;
                for (double X : {P.X,P.Y,P.Z,Q.X,Q.Y,Q.Z,Q.W}) V.Add(MakeShared<FJsonValueNumber>(X));
                Bones.Add(MakeShared<FJsonValueArray>(V));
            }
            F->SetArrayField(TEXT("component_bones"),Bones); Frames.Add''')
 f=f.replace('Root->SetStringField(TEXT("motion_profile"),TravelCm < 0 ? TEXT("fore-aft-pitch-roll-yaw") : TEXT("lateral-yaw"));','Root->SetStringField(TEXT("motion_profile"),TEXT("synthetic-articulated-animation-plus-component-motion"));')
 cpp.write_text(s+'\n'+f,encoding='utf8')
 at=h.rfind('};');h=h[:at]+'\n    UFUNCTION(BlueprintCallable, Category = "PBZModTools")\n    static FString TestClothAnimation(USkeletalMesh* Mesh, UAnimSequence* Animation, int32 Steps, float DeltaTime);\n'+h[at:];header.write_text(h,encoding='utf8')
host=W/'pose-tools-host';dst=host/'Plugins/PBZModTools';shutil.copytree(src,dst,dirs_exist_ok=True);project=host/'PoseTools.uproject';project.write_text(json.dumps({'FileVersion':3,'EngineAssociation':'5.7','Plugins':[{'Name':'PBZModTools','Enabled':True}]}))
UE=Path('F:/FTools/UE57/UE_5.7/Engine');cmd=[str(UE/'Binaries/ThirdParty/DotNet/8.0.412/win-x64/dotnet.exe'),str(UE/'Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll'),'UnrealEditor','Win64','Development','-Project='+str(project),'-Plugin='+str(dst/'PBZModTools.uplugin'),'-NoUBTMakefiles','-NoHotReload','-MaxParallelActions=1','-NoUBA','-NoXGE','-NoFASTBuild','-NoSNDBS']
with (W/'pose-tools-build.log').open('wb') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,DOTNET_PROCESSOR_COUNT='2',OMP_NUM_THREADS='1'),creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
(W/'pose-tools-build.json').write_text(json.dumps({'exit_code':p.returncode,'host':str(host),'one_action':True},indent=2));print('POSE_TOOLS_BUILD',p.returncode);raise SystemExit(p.returncode)
