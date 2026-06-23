function [codeOut] = codeGen(pattern0)
%%
% iBlock
% [ 4     2
%   3     1]
% iBit
% [7 3
%  6 2
%  5 1
%  4 0
% ]

isDriveBoard2MetaBoard_Reverse = [0 0 0 0];

fcn_2_code16x8 = {@(X) fliplr(rot90(X,0));
    @(X) fliplr(rot90(X,2));
    @(X) fliplr(X);
    @(X) fliplr((rot90(X,2)));};

fcn1 = @(x) (x);
fcn2 = @(x) fliplr(x);
fcn3 = @(x) fliplr(x);
fcn4 = @(x) (x);

pattern0(1:32,1:48) = fcn1(pattern0(1:32,1:48));
pattern0(32+(1:32),1:48) = fcn2(pattern0(32+(1:32),1:48));
pattern0(1:32,48+(1:48)) = fcn3(pattern0(1:32,48+(1:48)));
pattern0(32+(1:32),48+(1:48)) = fcn4(pattern0(32+(1:32),48+(1:48)));

A = pattern0(1:32,1:2:48);
pattern0(1:32,1:2:48) = pattern0(1:32,2:2:48);
pattern0(1:32,2:2:48) = A;


A = pattern0(32+(1:32),48+(1:2:48));
pattern0(32+(1:32),48+(1:2:48)) = pattern0(32+(1:32),48+(2:2:48));
pattern0(32+(1:32),48+(2:2:48)) = A;


%%
pattern0_7 = repmat(pattern0,[1 1 7]);
patternN = 7;
%%
Y_INDEX = {1:16;17:32;33:48;49:64};Y_INDEX = [Y_INDEX;Y_INDEX];
X_INDEX = {1:48;49:96}; X_INDEX = X_INDEX([1 1 1 1 2 2 2 2]);

%%
codeOut = zeros(8,768 * 7);

[connectorPin2metaunitPos,metaunitPos2connectorPin] = META_2023_3p5GHz_BlueFR4_Mapping();
[connectorPin2bitPos,bitPos2connectorPin] = MCU_2023_8bitShiftReg_128Pin_Mapping();


for iN = 1:patternN

    for iBit = 1:8
        % iBlock = 1 / 2 / 3 / 4
        iBlock = ceil(iBit/2);

        if(~isDriveBoard2MetaBoard_Reverse(iBlock))
            iBitPos2iLoc = connectorPin2metaunitPos(bitPos2connectorPin(1:128));
        else
            iBitPos2iLoc = connectorPin2metaunitPos(bitPos2connectorPin(128:-1:1));
        end

        pattern_block = pattern0_7(Y_INDEX{iBit},X_INDEX{iBit},iN);

        pattern_block = reshape(pattern_block, [16,8,6]);

        bitStream = zeros(128,6);
        for iCascade = 1:6
            if(ismember(iBlock,[1 3]))
                X = pattern_block(:,:,iCascade);
            else
                X = pattern_block(:,:,7-iCascade);
            end

            X = fcn_2_code16x8{iBlock}(X);

            bitStream(:,iCascade) = X(iBitPos2iLoc(1:128));
        end
        bitStream = reshape(bitStream,768,1);

        codeOut(iBit, (1:768)+(iN-1)*768) = bitStream;
    end
end

end

