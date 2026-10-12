#include "area_scan_3d_camera/ParameterInclude.h"
#include "bindings.h"
void bind_descriptors(nb::module_ &m) {
    nb::dict descriptors;
    {
        nb::dict d;
        d["name"] = nb::cast(eye::laser_setting::PowerLevel::name);
        d["description"] = nb::cast(eye::laser_setting::PowerLevel::description);
        d["type"] = nb::cast(int(eye::laser_setting::PowerLevel::type));
        d["unit"] = nb::cast(eye::laser_setting::PowerLevel::unit);
        d["step"] = nb::cast(eye::laser_setting::PowerLevel::step());
        d["range"] = nb::cast(eye::laser_setting::PowerLevel::range());
        descriptors["LaserPowerLevel"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::laser_setting::FringeCodingMode::name);
        d["description"] = nb::cast(eye::laser_setting::FringeCodingMode::description);
        d["type"] = nb::cast(int(eye::laser_setting::FringeCodingMode::type));
        d["Value_Fast"] = int(eye::laser_setting::FringeCodingMode::Value::Fast);
        d["Value_Accurate"] = int(eye::laser_setting::FringeCodingMode::Value::Accurate);
        d["Value_Reflective"] = int(eye::laser_setting::FringeCodingMode::Value::Reflective);
        descriptors["LaserFringeCodingMode"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::laser_setting::ProcessingMode::name);
        d["description"] = nb::cast(eye::laser_setting::ProcessingMode::description);
        d["type"] = nb::cast(int(eye::laser_setting::ProcessingMode::type));
        d["Value_Faster"] = int(eye::laser_setting::ProcessingMode::Value::Faster);
        d["Value_MoreComplete"] = int(eye::laser_setting::ProcessingMode::Value::MoreComplete);
        descriptors["ProcessingMode"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::laser_setting::FrameRange::name);
        d["description"] = nb::cast(eye::laser_setting::FrameRange::description);
        d["type"] = nb::cast(int(eye::laser_setting::FrameRange::type));
        d["range"] = nb::cast(eye::laser_setting::FrameRange::range());
        descriptors["LaserFrameRange"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::laser_setting::FramePartitionCount::name);
        d["description"] = nb::cast(eye::laser_setting::FramePartitionCount::description);
        d["type"] = nb::cast(int(eye::laser_setting::FramePartitionCount::type));
        d["range"] = nb::cast(eye::laser_setting::FramePartitionCount::range());
        descriptors["LaserFramePartitionCount"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::SurfaceSmoothing::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::SurfaceSmoothing::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::SurfaceSmoothing::type));
        d["Value_Off"] = int(eye::pointcloud_processing_setting::SurfaceSmoothing::Value::Off);
        d["Value_Weak"] = int(eye::pointcloud_processing_setting::SurfaceSmoothing::Value::Weak);
        d["Value_Normal"] =
            int(eye::pointcloud_processing_setting::SurfaceSmoothing::Value::Normal);
        d["Value_Strong"] =
            int(eye::pointcloud_processing_setting::SurfaceSmoothing::Value::Strong);
        descriptors["PointCloudSurfaceSmoothing"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::NoiseRemoval::name);
        d["description"] = nb::cast(eye::pointcloud_processing_setting::NoiseRemoval::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::NoiseRemoval::type));
        d["Value_Off"] = int(eye::pointcloud_processing_setting::NoiseRemoval::Value::Off);
        d["Value_Weak"] = int(eye::pointcloud_processing_setting::NoiseRemoval::Value::Weak);
        d["Value_Normal"] = int(eye::pointcloud_processing_setting::NoiseRemoval::Value::Normal);
        d["Value_Strong"] = int(eye::pointcloud_processing_setting::NoiseRemoval::Value::Strong);
        descriptors["PointCloudNoiseRemoval"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::DepthSmooth::name);
        d["description"] = nb::cast(eye::pointcloud_processing_setting::DepthSmooth::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::DepthSmooth::type));
        d["Value_Off"] = int(eye::pointcloud_processing_setting::DepthSmooth::Value::Off);
        d["Value_Weak"] = int(eye::pointcloud_processing_setting::DepthSmooth::Value::Weak);
        d["Value_Normal"] = int(eye::pointcloud_processing_setting::DepthSmooth::Value::Normal);
        d["Value_Strong"] = int(eye::pointcloud_processing_setting::DepthSmooth::Value::Strong);
        descriptors["PointCloudDepthSmooth"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::DepthHoleFilling::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::DepthHoleFilling::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::DepthHoleFilling::type));
        d["Value_Off"] = int(eye::pointcloud_processing_setting::DepthHoleFilling::Value::Off);
        d["Value_Weak"] = int(eye::pointcloud_processing_setting::DepthHoleFilling::Value::Weak);
        d["Value_Normal"] =
            int(eye::pointcloud_processing_setting::DepthHoleFilling::Value::Normal);
        d["Value_Strong"] =
            int(eye::pointcloud_processing_setting::DepthHoleFilling::Value::Strong);
        descriptors["PointCloudDepthHoleFilling"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::DepthSurfaceNoiseRemoval::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::DepthSurfaceNoiseRemoval::description);
        d["type"] =
            nb::cast(int(eye::pointcloud_processing_setting::DepthSurfaceNoiseRemoval::type));
        d["Value_Off"] =
            int(eye::pointcloud_processing_setting::DepthSurfaceNoiseRemoval::Value::Off);
        d["Value_Weak"] =
            int(eye::pointcloud_processing_setting::DepthSurfaceNoiseRemoval::Value::Weak);
        d["Value_Normal"] =
            int(eye::pointcloud_processing_setting::DepthSurfaceNoiseRemoval::Value::Normal);
        d["Value_Strong"] =
            int(eye::pointcloud_processing_setting::DepthSurfaceNoiseRemoval::Value::Strong);
        descriptors["PointCloudDepthSurfaceNoiseRemoval"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::description);
        d["type"] =
            nb::cast(int(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::type));
        d["Value_L0"] =
            int(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::Value::L0);
        d["Value_L1"] =
            int(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::Value::L1);
        d["Value_L2"] =
            int(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::Value::L2);
        d["Value_L3"] =
            int(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::Value::L3);
        d["Value_L4"] =
            int(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::Value::L4);
        d["Value_L5"] =
            int(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::Value::L5);
        d["Value_L6"] =
            int(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::Value::L6);
        d["Value_L7"] =
            int(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::Value::L7);
        d["Value_L8"] =
            int(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::Value::L8);
        d["Value_L9"] =
            int(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::Value::L9);
        d["Value_L10"] =
            int(eye::pointcloud_processing_setting::PhaseClusterOutlierRemoval::Value::L10);
        descriptors["PointCloudPhaseClusterOutlierRemoval"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::SpuriousPhaseRemoval::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::SpuriousPhaseRemoval::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::SpuriousPhaseRemoval::type));
        d["Value_Off"] = int(eye::pointcloud_processing_setting::SpuriousPhaseRemoval::Value::Off);
        d["Value_Weak"] =
            int(eye::pointcloud_processing_setting::SpuriousPhaseRemoval::Value::Weak);
        d["Value_Normal"] =
            int(eye::pointcloud_processing_setting::SpuriousPhaseRemoval::Value::Normal);
        d["Value_Strong"] =
            int(eye::pointcloud_processing_setting::SpuriousPhaseRemoval::Value::Strong);
        descriptors["PointCloudSpuriousPhaseRemoval"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::LargeGradNoiseRemoval::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::LargeGradNoiseRemoval::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::LargeGradNoiseRemoval::type));
        d["Value_Off"] = int(eye::pointcloud_processing_setting::LargeGradNoiseRemoval::Value::Off);
        d["Value_Weak"] =
            int(eye::pointcloud_processing_setting::LargeGradNoiseRemoval::Value::Weak);
        d["Value_Normal"] =
            int(eye::pointcloud_processing_setting::LargeGradNoiseRemoval::Value::Normal);
        d["Value_Strong"] =
            int(eye::pointcloud_processing_setting::LargeGradNoiseRemoval::Value::Strong);
        descriptors["PointCloudLargeGradNoiseRemoval"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::OutlierRemoval::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::OutlierRemoval::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::OutlierRemoval::type));
        d["Value_Off"] = int(eye::pointcloud_processing_setting::OutlierRemoval::Value::Off);
        d["Value_Weak"] = int(eye::pointcloud_processing_setting::OutlierRemoval::Value::Weak);
        d["Value_Normal"] = int(eye::pointcloud_processing_setting::OutlierRemoval::Value::Normal);
        d["Value_Strong"] = int(eye::pointcloud_processing_setting::OutlierRemoval::Value::Strong);
        descriptors["PointCloudOutlierRemoval"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::GapFilling::name);
        d["description"] = nb::cast(eye::pointcloud_processing_setting::GapFilling::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::GapFilling::type));
        d["Value_Off"] = int(eye::pointcloud_processing_setting::GapFilling::Value::Off);
        d["Value_Weak"] = int(eye::pointcloud_processing_setting::GapFilling::Value::Weak);
        d["Value_Normal"] = int(eye::pointcloud_processing_setting::GapFilling::Value::Normal);
        d["Value_Strong"] = int(eye::pointcloud_processing_setting::GapFilling::Value::Strong);
        descriptors["GapFilling"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::EdgePreservation::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::EdgePreservation::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::EdgePreservation::type));
        d["Value_Sharp"] = int(eye::pointcloud_processing_setting::EdgePreservation::Value::Sharp);
        d["Value_Normal"] =
            int(eye::pointcloud_processing_setting::EdgePreservation::Value::Normal);
        d["Value_Smooth"] =
            int(eye::pointcloud_processing_setting::EdgePreservation::Value::Smooth);
        descriptors["PointCloudEdgePreservation"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::EnableDistortionCorrection::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::EnableDistortionCorrection::description);
        d["type"] =
            nb::cast(int(eye::pointcloud_processing_setting::EnableDistortionCorrection::type));
        descriptors["EnableDistortionCorrection"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::DistortionCorrection::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::DistortionCorrection::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::DistortionCorrection::type));
        d["unit"] = nb::cast(eye::pointcloud_processing_setting::DistortionCorrection::unit);
        d["range"] = nb::cast(eye::pointcloud_processing_setting::DistortionCorrection::range());
        descriptors["DistortionCorrection"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::FringeContrastThreshold::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::FringeContrastThreshold::description);
        d["type"] =
            nb::cast(int(eye::pointcloud_processing_setting::FringeContrastThreshold::type));
        d["unit"] = nb::cast(eye::pointcloud_processing_setting::FringeContrastThreshold::unit);
        d["range"] = nb::cast(eye::pointcloud_processing_setting::FringeContrastThreshold::range());
        descriptors["PointCloudFringeContrastThreshold"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::FringeMinThreshold::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::FringeMinThreshold::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::FringeMinThreshold::type));
        d["unit"] = nb::cast(eye::pointcloud_processing_setting::FringeMinThreshold::unit);
        d["range"] = nb::cast(eye::pointcloud_processing_setting::FringeMinThreshold::range());
        descriptors["PointCloudFringeMinThreshold"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::EdgeArtifactRemoval::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::EdgeArtifactRemoval::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::EdgeArtifactRemoval::type));
        descriptors["EdgeArtifactRemoval"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::EnableGapFilling::name);
        d["description"] =
            nb::cast(eye::pointcloud_processing_setting::EnableGapFilling::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::EnableGapFilling::type));
        descriptors["EnableGapFilling"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::pointcloud_processing_setting::GapSize::name);
        d["description"] = nb::cast(eye::pointcloud_processing_setting::GapSize::description);
        d["type"] = nb::cast(int(eye::pointcloud_processing_setting::GapSize::type));
        d["unit"] = nb::cast(eye::pointcloud_processing_setting::GapSize::unit);
        d["range"] = nb::cast(eye::pointcloud_processing_setting::GapSize::range());
        descriptors["GapSize"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::projector_setting::PowerLevel::name);
        d["description"] = nb::cast(eye::projector_setting::PowerLevel::description);
        d["type"] = nb::cast(int(eye::projector_setting::PowerLevel::type));
        d["Value_High"] = int(eye::projector_setting::PowerLevel::Value::High);
        d["Value_Normal"] = int(eye::projector_setting::PowerLevel::Value::Normal);
        d["Value_Low"] = int(eye::projector_setting::PowerLevel::Value::Low);
        descriptors["ProjectorPowerLevel"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::projector_setting::FringeCodingMode::name);
        d["description"] = nb::cast(eye::projector_setting::FringeCodingMode::description);
        d["type"] = nb::cast(int(eye::projector_setting::FringeCodingMode::type));
        d["Value_Fast"] = int(eye::projector_setting::FringeCodingMode::Value::Fast);
        d["Value_Accurate"] = int(eye::projector_setting::FringeCodingMode::Value::Accurate);
        d["Value_Translucent"] = int(eye::projector_setting::FringeCodingMode::Value::Translucent);
        d["Value_Reflective"] = int(eye::projector_setting::FringeCodingMode::Value::Reflective);
        descriptors["ProjectorFringeCodingMode"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::projector_setting::AntiFlickerMode::name);
        d["description"] = nb::cast(eye::projector_setting::AntiFlickerMode::description);
        d["type"] = nb::cast(int(eye::projector_setting::AntiFlickerMode::type));
        d["Value_Off"] = int(eye::projector_setting::AntiFlickerMode::Value::Off);
        d["Value_AC50Hz"] = int(eye::projector_setting::AntiFlickerMode::Value::AC50Hz);
        d["Value_AC60Hz"] = int(eye::projector_setting::AntiFlickerMode::Value::AC60Hz);
        descriptors["AntiFlickerMode"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::projector_setting::InterferenceSuppression::name);
        d["description"] = nb::cast(eye::projector_setting::InterferenceSuppression::description);
        d["type"] = nb::cast(int(eye::projector_setting::InterferenceSuppression::type));
        descriptors["ProjectorInterferenceSuppression"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::projector_setting::ProcessingMode::name);
        d["description"] = nb::cast(eye::projector_setting::ProcessingMode::description);
        d["type"] = nb::cast(int(eye::projector_setting::ProcessingMode::type));
        d["Value_Faster"] = int(eye::projector_setting::ProcessingMode::Value::Faster);
        d["Value_MoreComplete"] = int(eye::projector_setting::ProcessingMode::Value::MoreComplete);
        d["Value_MetalPlate"] = int(eye::projector_setting::ProcessingMode::Value::MetalPlate);
        descriptors["ProjectorProcessingMode"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::ExposureMode::name);
        d["description"] = nb::cast(eye::scanning2d_setting::ExposureMode::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::ExposureMode::type));
        d["Value_Timed"] = int(eye::scanning2d_setting::ExposureMode::Value::Timed);
        d["Value_Auto"] = int(eye::scanning2d_setting::ExposureMode::Value::Auto);
        d["Value_HDR"] = int(eye::scanning2d_setting::ExposureMode::Value::HDR);
        d["Value_Flash"] = int(eye::scanning2d_setting::ExposureMode::Value::Flash);
        descriptors["Scanning2DExposureMode"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::ExposureTime::name);
        d["description"] = nb::cast(eye::scanning2d_setting::ExposureTime::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::ExposureTime::type));
        d["unit"] = nb::cast(eye::scanning2d_setting::ExposureTime::unit);
        d["range"] = nb::cast(eye::scanning2d_setting::ExposureTime::range());
        descriptors["Scanning2DExposureTime"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::SharpenFactor::name);
        d["description"] = nb::cast(eye::scanning2d_setting::SharpenFactor::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::SharpenFactor::type));
        d["range"] = nb::cast(eye::scanning2d_setting::SharpenFactor::range());
        descriptors["Scanning2DSharpenFactor"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::ExpectedGrayValue::name);
        d["description"] = nb::cast(eye::scanning2d_setting::ExpectedGrayValue::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::ExpectedGrayValue::type));
        d["range"] = nb::cast(eye::scanning2d_setting::ExpectedGrayValue::range());
        descriptors["Scanning2DExpectedGrayValue"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::ToneMappingEnable::name);
        d["description"] = nb::cast(eye::scanning2d_setting::ToneMappingEnable::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::ToneMappingEnable::type));
        descriptors["Scanning2DToneMappingEnable"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::AutoExposureROI::name);
        d["description"] = nb::cast(eye::scanning2d_setting::AutoExposureROI::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::AutoExposureROI::type));
        descriptors["Scanning2DAutoExposureROI"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::HDRExposureSequence::name);
        d["description"] = nb::cast(eye::scanning2d_setting::HDRExposureSequence::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::HDRExposureSequence::type));
        d["unit"] = nb::cast(eye::scanning2d_setting::HDRExposureSequence::unit);
        d["range"] = nb::cast(eye::scanning2d_setting::HDRExposureSequence::range());
        d["max_size"] = nb::cast(eye::scanning2d_setting::HDRExposureSequence::maxSize());
        descriptors["Scanning2DHDRExposureSequence"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::DepthSourceExposureMode::name);
        d["description"] = nb::cast(eye::scanning2d_setting::DepthSourceExposureMode::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::DepthSourceExposureMode::type));
        d["Value_Timed"] = int(eye::scanning2d_setting::DepthSourceExposureMode::Value::Timed);
        d["Value_Flash"] = int(eye::scanning2d_setting::DepthSourceExposureMode::Value::Flash);
        descriptors["Scanning2DDepthSourceExposureMode"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::DepthSourceExposureTime::name);
        d["description"] = nb::cast(eye::scanning2d_setting::DepthSourceExposureTime::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::DepthSourceExposureTime::type));
        d["unit"] = nb::cast(eye::scanning2d_setting::DepthSourceExposureTime::unit);
        d["range"] = nb::cast(eye::scanning2d_setting::DepthSourceExposureTime::range());
        descriptors["Scanning2DDepthSourceExposureTime"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::FlashAcquisitionMode::name);
        d["description"] = nb::cast(eye::scanning2d_setting::FlashAcquisitionMode::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::FlashAcquisitionMode::type));
        d["Value_Responsive"] =
            int(eye::scanning2d_setting::FlashAcquisitionMode::Value::Responsive);
        d["Value_Fast"] = int(eye::scanning2d_setting::FlashAcquisitionMode::Value::Fast);
        descriptors["Scanning2DFlashAcquisitionMode"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::FlashExposureTime::name);
        d["description"] = nb::cast(eye::scanning2d_setting::FlashExposureTime::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::FlashExposureTime::type));
        d["unit"] = nb::cast(eye::scanning2d_setting::FlashExposureTime::unit);
        d["range"] = nb::cast(eye::scanning2d_setting::FlashExposureTime::range());
        descriptors["Scanning2DFlashExposureTime"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::Gain::name);
        d["description"] = nb::cast(eye::scanning2d_setting::Gain::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::Gain::type));
        d["unit"] = nb::cast(eye::scanning2d_setting::Gain::unit);
        d["range"] = nb::cast(eye::scanning2d_setting::Gain::range());
        descriptors["Scanning2DGain"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::PatternRoleGain::name);
        d["description"] = nb::cast(eye::scanning2d_setting::PatternRoleGain::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::PatternRoleGain::type));
        d["unit"] = nb::cast(eye::scanning2d_setting::PatternRoleGain::unit);
        d["range"] = nb::cast(eye::scanning2d_setting::PatternRoleGain::range());
        descriptors["Scanning2DPatternRoleGain"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::FlashGain::name);
        d["description"] = nb::cast(eye::scanning2d_setting::FlashGain::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::FlashGain::type));
        d["unit"] = nb::cast(eye::scanning2d_setting::FlashGain::unit);
        d["range"] = nb::cast(eye::scanning2d_setting::FlashGain::range());
        descriptors["Scanning2DFlashGain"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning2d_setting::FlashPowerLevel::name);
        d["description"] = nb::cast(eye::scanning2d_setting::FlashPowerLevel::description);
        d["type"] = nb::cast(int(eye::scanning2d_setting::FlashPowerLevel::type));
        d["unit"] = nb::cast(eye::scanning2d_setting::FlashPowerLevel::unit);
        d["range"] = nb::cast(eye::scanning2d_setting::FlashPowerLevel::range());
        descriptors["Scanning2DFlashPowerLevel"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning3d_setting::ExposureCount::name);
        d["description"] = nb::cast(eye::scanning3d_setting::ExposureCount::description);
        d["type"] = nb::cast(int(eye::scanning3d_setting::ExposureCount::type));
        d["range"] = nb::cast(eye::scanning3d_setting::ExposureCount::range());
        descriptors["Scanning3DExposureCount"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning3d_setting::ExposureSequence::name);
        d["description"] = nb::cast(eye::scanning3d_setting::ExposureSequence::description);
        d["type"] = nb::cast(int(eye::scanning3d_setting::ExposureSequence::type));
        d["unit"] = nb::cast(eye::scanning3d_setting::ExposureSequence::unit);
        d["range"] = nb::cast(eye::scanning3d_setting::ExposureSequence::range());
        d["max_size"] = nb::cast(eye::scanning3d_setting::ExposureSequence::maxSize());
        descriptors["Scanning3DExposureSequence"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning3d_setting::Gain::name);
        d["description"] = nb::cast(eye::scanning3d_setting::Gain::description);
        d["type"] = nb::cast(int(eye::scanning3d_setting::Gain::type));
        d["unit"] = nb::cast(eye::scanning3d_setting::Gain::unit);
        d["range"] = nb::cast(eye::scanning3d_setting::Gain::range());
        descriptors["Scanning3DGain"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning3d_setting::GroupExposureSelector::name);
        d["description"] = nb::cast(eye::scanning3d_setting::GroupExposureSelector::description);
        d["type"] = nb::cast(int(eye::scanning3d_setting::GroupExposureSelector::type));
        d["Value_Exposure1"] =
            int(eye::scanning3d_setting::GroupExposureSelector::Value::Exposure1);
        d["Value_Exposure2"] =
            int(eye::scanning3d_setting::GroupExposureSelector::Value::Exposure2);
        descriptors["Scanning3DGroupExposureSelector"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning3d_setting::GroupExposureTime::name);
        d["description"] = nb::cast(eye::scanning3d_setting::GroupExposureTime::description);
        d["type"] = nb::cast(int(eye::scanning3d_setting::GroupExposureTime::type));
        d["unit"] = nb::cast(eye::scanning3d_setting::GroupExposureTime::unit);
        d["range"] = nb::cast(eye::scanning3d_setting::GroupExposureTime::range());
        descriptors["Scanning3DGroupExposureTime"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning3d_setting::GroupGain::name);
        d["description"] = nb::cast(eye::scanning3d_setting::GroupGain::description);
        d["type"] = nb::cast(int(eye::scanning3d_setting::GroupGain::type));
        d["unit"] = nb::cast(eye::scanning3d_setting::GroupGain::unit);
        d["range"] = nb::cast(eye::scanning3d_setting::GroupGain::range());
        descriptors["Scanning3DGroupGain"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning3d_setting::GroupDlpPowerLevel::name);
        d["description"] = nb::cast(eye::scanning3d_setting::GroupDlpPowerLevel::description);
        d["type"] = nb::cast(int(eye::scanning3d_setting::GroupDlpPowerLevel::type));
        d["unit"] = nb::cast(eye::scanning3d_setting::GroupDlpPowerLevel::unit);
        d["range"] = nb::cast(eye::scanning3d_setting::GroupDlpPowerLevel::range());
        descriptors["Scanning3DGroupDlpPowerLevel"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning3d_setting::ROI::name);
        d["description"] = nb::cast(eye::scanning3d_setting::ROI::description);
        d["type"] = nb::cast(int(eye::scanning3d_setting::ROI::type));
        descriptors["Scanning3DROI"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::scanning3d_setting::DepthRange::name);
        d["description"] = nb::cast(eye::scanning3d_setting::DepthRange::description);
        d["type"] = nb::cast(int(eye::scanning3d_setting::DepthRange::type));
        d["unit"] = nb::cast(eye::scanning3d_setting::DepthRange::unit);
        d["range"] = nb::cast(eye::scanning3d_setting::DepthRange::range());
        descriptors["Scanning3DDepthRange"] = d;
    }
    {
        nb::dict d;
        d["name"] = nb::cast(eye::uhp_setting::CaptureMode::name);
        d["description"] = nb::cast(eye::uhp_setting::CaptureMode::description);
        d["type"] = nb::cast(int(eye::uhp_setting::CaptureMode::type));
        d["Value_Camera1"] = int(eye::uhp_setting::CaptureMode::Value::Camera1);
        d["Value_Camera2"] = int(eye::uhp_setting::CaptureMode::Value::Camera2);
        d["Value_Merge"] = int(eye::uhp_setting::CaptureMode::Value::Merge);
        descriptors["UhpCaptureMode"] = d;
    }
    m.attr("descriptors") = descriptors;
}